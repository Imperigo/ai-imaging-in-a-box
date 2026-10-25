"""SZENENNAHT — der Renderauftrag des Ökosystems, in unsere Felder und zurück.

Warum dieses Modul neben ``kosmo_naht.py`` steht
------------------------------------------------
``kosmo_naht`` übersetzt die **Auftragsverwaltung** (Kennung, Status, Freigabe-Token).
Hier geht es um den **Szenenvertrag**: was gerendert werden soll und was dabei
herauskam. Das ist eine eigene, deutlich grössere Fläche mit eigenen Fallen, und sie
gehört nicht in dieselbe Datei.

Die Verträge liegen als prüfbare Schemata in der Designzentrale
(``kosmovis.render-scene/v1`` und ``kosmovis.render-result/v2``). Sie sind hier
**wörtlich gelesen**, nicht aus einem Bericht abgeschrieben — ein Feldname, den man
errät, erzeugt in diesem Ökosystem keine Fehlermeldung, sondern eine tote Kante.

Die drei Stellen, an denen wir dem fremden Vertrag NICHT folgen
---------------------------------------------------------------
Das ist der eigentliche Inhalt dieses Moduls. Der fremde Vertrag ist gut gebaut, aber er
schreibt an drei Stellen Vorgabewerte fest, von denen wir inzwischen **gemessen** haben,
dass sie nicht stimmen. Sie stillschweigend zu bedienen hiesse, einen bekannten Fehler
in eine fremde Oberfläche zu tragen, wo ihn niemand mehr findet.

1. **Die Stil-Schwelle 0.30 und das Verfahren „dinov3".** Beides sind dort
   Vorgabewerte. Wir haben am 18.08.2026 an 4950 Bildpaaren gemessen, dass der Boden von
   SigLIP 2 bei **0.526** liegt — 0.30 lässt damit **jedes beliebige Bildpaar** durch
   (`auf-20260818-11`). Und unser Einbetter ist seit Sitzung 06 SigLIP 2, nicht DINOv3.
   Wir senden darum **unsere** Schwelle und **unser** Verfahren mit, nie deren Vorgabe.
   Das ist zulässig: Ein gesendetes Feld schlägt dort jeden Vorgabewert.

2. **Die Backbone-Liste kennt unser Modell nicht.** Sie führt ``qwen``,
   ``flux2-klein``, ``flux-krea``, ``sdxl``. Unser Vorgabe-Backbone (`z-image-turbo`,
   Apache-2.0, seit `auf-20260818-13` gemessen) steht dort **nicht**. Wir **raten
   nicht**, sondern melden die Lücke: :func:`backbone_nach_fremd` gibt ``None`` und eine
   Begründung zurück.

   *Berichtigung an mir selbst, 19.08.2026:* Hier stand zuerst, „zwei der vier Einträge
   sind FLUX und damit unter Regel 1 ausgeschlossen". **Das ist falsch.**
   ``flux2-klein`` ist **FLUX.2-klein und Apache-2.0**, also zulässig; ausgeschlossen ist
   allein ``flux-krea``, wofür wir folgerichtig gar keinen Registry-Eintrag haben. Ein
   Test hat die Behauptung gefangen, bevor sie ausgeliefert war — eine falsche Aussage
   über den Vertrag eines anderen wäre die peinlichste Sorte Fehler, und sie wäre in
   einem Docstring nie wieder aufgefallen.

3. **``faithful`` ist ein einzelner Regler von 0 bis 1.** Bei uns hängt „wie treu" an
   mindestens drei Grössen, und `auf-20260818-13` hat gemessen, dass die Wirkung **nicht
   monoton** ist: 0.80 schneidet besser ab als 1.00. Wir reichen den Wert an
   ``controlnet_staerke`` durch, weil das die einzige ehrliche Zuordnung ist, und
   vermerken, was dabei unter den Tisch fällt.

Abhängigkeiten: keine. Reine stdlib, kein ``bpy`` (Regel 2), aus Python heraus ohne
Oberfläche aufrufbar (Regel 4).
"""
from __future__ import annotations

import math
import re

from . import backbone as _backbone
from . import contracts as _contracts
from . import geometrie_qa, prompts, sprache, stil_qa
from . import gate as _gate
from . import kameras as _kameras
from . import raumkamera as _raumkamera
from . import sonne as _sonne
from . import materialwahl as _materialwahl
from . import stimmung as _stimmung
from . import umfeld as _umfeld

#: Die beiden Vertragskennungen, wörtlich aus den Schemadateien der Designzentrale.
#:
#: ``SCHEMA_SZENE`` ist die **einzige** Stelle dieser Kennung im Kern (Befund 22.09.2026):
#: ``kosmo_naht.SCHEMA_RENDER_SCENE`` hält seither dieses Objekt und keine eigene Kopie.
SCHEMA_SZENE = "kosmovis.render-scene/v1"
SCHEMA_ERGEBNIS = "kosmovis.render-result/v2"

#: Geometrieformate, die der fremde Vertrag zulässt.
FREMDE_FORMATE = ("glb", "gltf", "fbx", "blend", "ifc")

#: Formate, die UNSERE Kette wirklich verarbeitet. Der Rest wird angenommen und
#: abgelehnt — mit Begründung, nicht mit einem Absturz zwei Stufen später.
UNSERE_FORMATE = ("glb", "gltf", "ifc")

#: Die Backbone-Liste des fremden Vertrags, wörtlich.
#:
#: **``z-image-turbo`` ergänzt am 19.08.2026, und die Geschichte dazu gehört hierher.**
#: Bis dahin fehlte es *drüben*: Ihr Vertrag führte ``qwen`` als Vorgabe, obwohl
#: ``auf-20260818-09`` am Gerät belegt hat, dass ``QwenImageEditPlusPipeline`` kein
#: ControlNet ist. Das wurde gemeldet und eingebaut — und im nächsten Demolauf wies
#: **diese** Seite den neuen Namen ab, weil die Liste hier nicht mitgewachsen war.
#:
#: Die Zuordnung ist **zweiseitig und an zwei Orten von Hand gepflegt**. Wer eine Seite
#: ergänzt, hat die Naht noch nicht ergänzt; sie trägt erst, wenn beide es tun. Genau
#: diese Bauform hat am selben Tag vier widersprüchliche Massstabslisten und drei
#: Beschriftungsorte für dieselbe Station hervorgebracht.
FREMDE_BACKBONES = ("qwen", "flux2-klein", "flux-krea", "sdxl", "z-image-turbo")

#: Zuordnung fremd → unsere Registry, soweit sie trägt.
#:
#: ``flux-krea`` fehlt bewusst: Es ist ein FLUX-Ableger und damit unter Regel 1
#: ausgeschlossen; wir haben keinen Eintrag dafür und sollen auch keinen bekommen.
BACKBONE_VON_FREMD = {
    "qwen": "qwen-image-edit-2511",
    "flux2-klein": "flux2-klein-4b",
    "sdxl": "sdxl-juggernaut",
    # Gleicher Name auf beiden Seiten — die Zuordnung ist hier die Identität. Sie steht
    # trotzdem ausgeschrieben da: Ein Eintrag, der fehlt, sieht von aussen genauso aus
    # wie ein Name, den es nicht gibt.
    "z-image-turbo": "z-image-turbo",
    # E128 (30.09.2026): regulär bestellbar, Lizenz offen. Ihr Vertrag kennt den Namen
    # noch nicht — gestellt als Vertragsfrage (erg-20260930-e128-vertragsfrage-qwen21.md).
    # Bis sie ihn einbauen, weist ihr eigenes Schema eine solche Bestellung vorher ab.
    "qwen-image-2.1": "qwen-image-2.1",
}

#: Die Auftragskennung der fremden Warteschlange — wörtlich aus ihrem Schema.
#: Ein Auftrag mit abweichender Kennung wird dort abgewiesen.
#:
#: **DIE EINE QUELLE, und bis zum 22.09.2026 waren es drei** (Befund 22.09.2026):
#: Dieselbe Regel stand als eigene Kopie in :data:`aiimaging.bruecke.VERZEICHNIS_MUSTER`
#: und in :data:`aiimaging.kosmo_naht.FREMDES_JOB_ID_MUSTER`, und keine las die andere —
#: obwohl ``bruecke`` dieses Modul längst einführte.
#:
#: Was das kostet, wenn die fremde Warteschlange ihre Kennungsform weitet: Geändert wird
#: die Stelle, an der der Vertrag geprüft wird — also :func:`pruefe_job_id` hier.
#: ``bruecke.offene_auftraege`` filterte danach weiter mit dem alten Muster und übergeht
#: den neuen Auftragsordner **stillschweigend**: kein Fehler, keine Warnung, der Auftrag
#: bleibt liegen. Genau die Sorte Lücke, gegen die dieses Projekt sonst baut.
#:
#: Die Regel trägt hier, weil hier der Vertrag geprüft wird. Gelesen wird sie auf
#: **zwei verschiedene Arten**, und wer sie weitet, muss beide kennen:
#:
#: * ``bruecke`` fragt :func:`ist_fremde_job_id` bei **jedem Aufruf** — eine Änderung an
#:   der Funktion erreicht die Auftragsordner drüben sofort.
#: * ``kosmo_naht.FREMDES_JOB_ID_MUSTER`` hält **dieses Musterobjekt**, gebunden beim
#:   Laden. Wer nur die Funktion ändert, ändert die Auskunft der Naht nicht mit.
#:
#: Geweitet wird darum **hier, an diesem Muster** — dann folgen Funktion und Naht beide.
FREMDE_JOB_ID = re.compile(r"^vis-\d+-[0-9a-f]{6}$")

#: Die Kennung einer Blender-Grundlage (Owner-Grundsatz Nr. 85, Demolauf 16.10.2026; Vertrag
#: mit dem Integrator 20.10.2026): ``gl-`` und 16 Hexzeichen. Vergeben vom Heim-PC, nie von
#: der bestellenden Seite — sie reicht nur zurueck, was sie bekommen hat.
GRUNDLAGE_KENNUNG = re.compile(r"^gl-[0-9a-f]{16}$")

#: Die Spanne von ``vis.seed`` — die des Integrators (Auflage 2, 20.10.2026): eine ganze Zahl
#: 0..2147483647, damit das Werkzeugschema ohne Sonderfall auskommt.
SEED_HOECHSTENS = 2147483647

#: Die Güten des Schalters am Render-Knoten (Owner-Entscheid 104, 20.10.2026), im Vertrag als
#: ``vis.guete``. Fehlt das Feld, gilt «voll» — so rechnet jeder Auftrag von vor dem Schalter.
GUETEN = _backbone.GUETEN
GUETE_VORSCHAU = _backbone.GUETE_VORSCHAU
GUETE_VOLL = _backbone.GUETE_VOLL

#: Unter diesem Schlüssel trägt ein Kameraurteil, was die Güte an der Rechnung geändert hat
#: (Bildmodell, Schritte, Startwert, Grösse). ``None`` heisst: volle Güte, nichts geändert.
URTEIL_GUETE = "guete_vermerk"


def ist_fremde_job_id(wert) -> bool:
    """Trägt dieser Text die Kennungsform der fremden Warteschlange?

    Die **einzige** Stelle, an der diese Frage beantwortet wird — siehe
    :data:`FREMDE_JOB_ID` für den Befund dahinter.

    Gefragt wird sowohl nach einer Auftragskennung (:func:`pruefe_job_id`) als auch nach
    einem **Ordnernamen** (``bruecke``). Das ist dieselbe Frage und nicht zufällig
    dieselbe Antwort: Die fremde Brücke benennt das Auftragsverzeichnis nach der Kennung
    des Auftrags, der darin liegt.

    Args:
        wert: Irgendetwas. Was kein Text ist, kann die Form nicht tragen — das ist ein
            ``False`` und kein Fehler.
    """
    return isinstance(wert, str) and FREMDE_JOB_ID.match(wert) is not None

#: Sensorbreite für die Umrechnung Brennweite ↔ Bildwinkel. Dieselbe wie in
#: :mod:`aiimaging.kameras` — zwei verschiedene Sensorbreiten an zwei Stellen wären ein
#: stiller Massstabsfehler.
SENSOR_BREITE_MM = 36.0

#: Grenzen des fremden ``fov``-Feldes, wörtlich: ``min(10).max(120)``.
FOV_MIN_GRAD = 10.0
FOV_MAX_GRAD = 120.0


class SzenenError(ValueError):
    """Der fremde Auftrag ist unbrauchbar, oder unsere Antwort passte nicht in ihn.

    Erbt von ``ValueError`` — dieselbe Entscheidung wie bei allen Fehlerklassen dieses
    Projekts, damit bestehendes ``except ValueError`` greift.
    """


#: Was ein Leser von :func:`lies_szene` fangen muss, damit ein unlesbarer Auftrag nur
#: sich selbst aufhaelt und nicht den ganzen Abholdurchgang (Runde 7c, 23.09.2026).
#:
#: Die erste Linie ist :func:`lies_szene` selbst: Jede Zahl geht durch
#: :func:`lies_zahl`, ein unlesbares Feld wird ein Mangel mit Satz. Diese Liste ist die
#: zweite Linie — die Fehlerarten, die ein unlesbares Feld in Python ausloest, wenn die
#: erste Linie etwas uebersieht: auch ``AttributeError`` (ein Block, der keiner ist),
#: ``ArithmeticError`` (darunter ``OverflowError``) und ``LookupError`` (darunter
#: ``KeyError``).
#:
#: **Der Befund dazu:** ``bruecke.lies_auftrag`` fing seit der Runde 7b diese sechs,
#: ``eigene_quelle.lies_auftrag`` nur die ersten drei. ``samples`` mit 400 Stellen warf
#: ``OverflowError`` aus ``lies_zahl`` und riss ueber die eigene Ablage
#: ``abholer.durchgang`` heraus. Beide Wege fangen darum dieselben — ``eigene_quelle``
#: liest sie hier; ``bruecke`` fuehrt sie heute noch als eigene Aufzaehlung mit gleichem
#: Inhalt. Dass beide Wege dieselben fangen, prueft
#: ``tests/test_runde7b_einlass.py`` mit derselben Attrappenliste auf beiden Wegen.
LESEFEHLER = (SzenenError, ValueError, TypeError, AttributeError, ArithmeticError,
              LookupError)


# --------------------------------------------------------------------------------------
# Brennweite ↔ Bildwinkel
# --------------------------------------------------------------------------------------

def _lies_kamerapunkt(punkt, wer: str, feld: str) -> tuple[float, float, float]:
    """Ein Kamerapunkt der Bestellung — drei echte, endliche Zahlen, sonst ``SzenenError``.

    **Die eine Pruefung fuer alle drei Kamerafunktionen** (Runde 9, 23.09.2026). Bis
    dahin stand sie dreimal, jede Fassung mit ``float(...)`` — und damit zwei Befunde:

    * ``float`` nimmt ``True`` und ``'5'`` an. ``kamera_zu_spec(auge=[True, '5', 0])``
      ergab ``position [1.0, 5.0, 0.0]``; ``spec_zu_kamera`` und ``kamera_nach_blender``
      ebenso. Dieselbe Fehlerart, die :func:`lies_zahl` fuer ``render.*`` seit der Runde
      7 abweist. Jede Koordinate geht darum durch :func:`lies_zahl` (``ganzzahlig=False``,
      ohne Bereich) — eine Regel, nicht vier.

      *Ob KosmoOrbit Koordinaten je als Text schickt, wurde vorher nachgelesen*
      (23.09.2026): In keiner der uebertragenen Antworten
      (``auftraege/ergebnisse/ANTWORT-*``), keinem abgelegten Auftrag und keinem Dokument
      steht eine ``position`` oder ein ``target`` mit Text; der einzige Treffer ist unser
      eigener Gegentest ``[0, 0, "x"]``. Die Kameras des Demolaufs 12 kamen als Zahlen.
      Ein Text wuerde also nichts brechen, was heute ankommt — und angenommen hiesse er,
      eine Zahl zu raten.
    * Die Form wurde mit ``repr`` der ganzen Liste gemeldet: ``auge`` mit VIER Eintraegen,
      einer davon eine ganze Zahl mit ueber 4300 Stellen, warf aus dem Satz selbst einen
      nackten ``ValueError`` statt ``SzenenError``. Seither :func:`_zeige_punkt`.

    Args:
        punkt: der Punkt, wie er ankam.
        wer: Satzanfang, z. B. ``"Kamera 'auge'"``.
        feld: Name fuer den Satz aus :func:`lies_zahl` (``auge[0]`` …).

    Raises:
        SzenenError: keine Liste aus drei Eintraegen, ein Eintrag keine Zahl (Text,
            Wahrheitswert, Block, eine ganze Zahl jenseits des Gleitkommabereichs), oder
            nicht endlich.
    """
    if not isinstance(punkt, (list, tuple)) or len(punkt) != 3:
        raise SzenenError(f"{wer} ist kein Punkt aus drei Zahlen: {_zeige_punkt(punkt)}")
    zahlen = []
    for k, wert in enumerate(punkt):
        zahl, satz = lies_zahl(wert, f"{feld}[{k}]", ganzzahlig=False)
        if satz:
            # Ein `float` ist eine Zahl, nur keine endliche; alles andere (auch eine
            # ganze Zahl jenseits des Gleitkommabereichs) laesst sich nicht rechnen.
            art = "keine endlichen Zahlen" if isinstance(wert, float) else "keine Zahlen"
            raise SzenenError(f"{wer} enthält {art}: {_zeige_punkt(punkt)}. {satz}")
        zahlen.append(zahl)
    return tuple(zahlen)


def _als_float(wert) -> float:
    """Eine schon als Zahl gepruefte Angabe als ``float`` — ``inf`` statt ``OverflowError``.

    Eine ganze Zahl jenseits des Gleitkommabereichs ist fuer die Pruefung dahinter
    dasselbe wie eine unendliche: nicht endlich, also ``SzenenError`` mit Satz (Runde 7c,
    23.09.2026).
    """
    try:
        return float(wert)
    except OverflowError:
        return math.inf if wert > 0 else -math.inf


def brennweite_zu_fov(brennweite_mm: float) -> float:
    """Brennweite in mm → **horizontaler** Bildwinkel in Grad.

    Warum ausdrücklich horizontal
    -----------------------------
    Der fremde Vertrag nennt sein Feld schlicht ``fov`` und sagt **nicht**, um welche
    Achse es geht. Das ist die gefährlichste Sorte Unklarheit: Beide Lesarten liefern
    eine plausible Zahl, und der Unterschied bei einem 16:9-Bild ist fast ein Faktor
    zwei. Wir legen uns auf **horizontal** fest, weil das die verbreitete Lesart bei
    Werkzeugen ist, die eine einzelne Zahl führen — und weil unsere eigene
    Abstandsrechnung horizontal beginnt (:func:`aiimaging.kameras.bildwinkel`).

    **Diese Festlegung ist eine Annahme und keine Messung.** Sie gehört an der ersten
    echten Naht überprüft: Ein um den Faktor zwei falscher Bildwinkel fällt an einem
    einzelnen Bild nicht auf, sondern erst, wenn jemand zwei Bilder nebeneinanderlegt.

    Raises:
        SzenenError: Brennweite nicht positiv-endlich.
    """
    if isinstance(brennweite_mm, bool) or not isinstance(brennweite_mm, (int, float)):
        raise SzenenError(f"brennweite_mm muss eine Zahl sein, war: {brennweite_mm!r}")
    # Eine riesige ganze Zahl warf hier OverflowError aus `float` (Runde 7c, 23.09.2026).
    f = _als_float(brennweite_mm)
    if not math.isfinite(f) or f <= 0.0:
        raise SzenenError(
            f"brennweite_mm muss positiv und endlich sein, war: {_zeige(brennweite_mm)}")
    return math.degrees(2.0 * math.atan(SENSOR_BREITE_MM / (2.0 * f)))


def fov_zu_brennweite(fov_grad: float) -> float:
    """Horizontaler Bildwinkel in Grad → Brennweite in mm. Die Umkehrung von oben.

    Raises:
        SzenenError: Winkel ausserhalb ``(0, 180)``. Bei 0 wäre die Brennweite
            unendlich, bei 180 null — beides sind keine Objektive.
    """
    if isinstance(fov_grad, bool) or not isinstance(fov_grad, (int, float)):
        raise SzenenError(f"fov muss eine Zahl sein, war: {fov_grad!r}")
    w = _als_float(fov_grad)
    if not math.isfinite(w) or not (0.0 < w < 180.0):
        raise SzenenError(
            f"fov muss zwischen 0 und 180 Grad liegen, war: {_zeige(fov_grad)}")
    return SENSOR_BREITE_MM / (2.0 * math.tan(math.radians(w) / 2.0))


def kamera_zu_spec(kamera: dict) -> dict:
    """Eine Kamera aus :func:`aiimaging.kameras.kamerasatz` → fremde ``CameraSpec``.

    Ihre Felder heissen ``name``, ``position``, ``target``, ``fov``; unsere ``kuerzel``,
    ``auge``, ``blick_auf``, ``brennweite_mm``. Die Umrechnung ist verlustfrei bis auf
    den Bildwinkel — siehe :func:`brennweite_zu_fov`.

    Raises:
        SzenenError: Der Bildwinkel fällt aus ihrer Spanne (10–120°). Das ist kein
            Rundungsfall: Ihr Schema **weist ihn ab**, und ein abgewiesener Auftrag zwei
            Stufen später ist teurer als ein Fehler hier. Ebenso, wenn ``auge`` oder
            ``blick_auf`` keine drei endlichen Zahlen sind (seit der Runde 8) — und
            seit der Runde 9 auch bei ``True`` oder ``'5'`` als Koordinate und bei einer
            Kamera, die kein Woerterbuch ist.
    """
    if not isinstance(kamera, dict):
        raise SzenenError(f"Kamera ist kein Wörterbuch: {type(kamera).__name__}")
    # Die Punkte ZUERST und ueber die eine Pruefung (Runde 9, 23.09.2026, siehe
    # `_lies_kamerapunkt`): nur echte, endliche Zahlen, und ein Satz, der selbst nicht
    # wirft. Vorher stand hier eine eigene Fassung mit `float(...)`.
    position = list(_lies_kamerapunkt(kamera.get("auge"), "Kamera 'auge'", "auge"))
    ziel = list(_lies_kamerapunkt(kamera.get("blick_auf"), "Kamera 'blick_auf'",
                                  "blick_auf"))

    # Der Rückfall ist die VORGABE aus `kameras`, keine abgeschriebene Zahl. Hier stand
    # bis zum 23.08.2026 fest `28.0` — als der Owner die Vorgabe auf 35 mm setzte, wäre
    # eine Kamera ohne eigene Brennweite still mit 28 mm in den fremden Vertrag gegangen,
    # während gerendert wurde mit 35. Zwei Zahlen für dieselbe Optik, und kein Test hätte
    # angeschlagen.
    fov = brennweite_zu_fov(kamera.get("brennweite_mm", _kameras.BRENNWEITE_MM))
    if not (FOV_MIN_GRAD <= fov <= FOV_MAX_GRAD):
        raise SzenenError(
            f"Brennweite {kamera.get('brennweite_mm')} mm ergibt {fov:.1f}° — der fremde "
            f"Vertrag lässt nur {FOV_MIN_GRAD:.0f}–{FOV_MAX_GRAD:.0f}° zu und würde den "
            f"Auftrag abweisen. Entweder die Brennweite ändern oder die Naht nicht nehmen."
        )
    # NICHT ENDLICH IST KEIN STANDPUNKT — auch in dieser Richtung (Runde 8, 23.09.2026):
    # `auge [inf, 0, 0]` ging hier still als `position [inf, …]` in eine CameraSpec. Das
    # prueft seit der Runde 9 `_lies_kamerapunkt` oben, fuer alle drei Funktionen gleich.
    return {
        "name": kamera.get("kuerzel"),
        "position": position,
        "target": ziel,
        "fov": fov,
        # PFLICHTFELD IHRES VERTRAGS, und es fehlte hier. `CameraSpec.up_axis` ist
        # `z.enum(['y','z'])` OHNE Default (P-ACHSENRIEGEL, 26.08.2026) — eine Spec
        # ohne dieses Feld wird von ihrem eigenen Schema ABGEWIESEN. Wir haben also
        # bis zum 01.09.2026 CameraSpecs gebaut, die drueben gar nicht durchkommen.
        #
        # `"z"` ist die richtige Angabe und keine Wahl: `kameras.kamerasatz` rechnet
        # aus der Huellbox, die der Blender-Bericht meldet, und die steht in Blenders
        # Weltsystem — Z oben. Unsere Zahlen sind Z-up, also sagen wir Z-up.
        "up_axis": HOCHACHSE_BLENDER,
    }


#: Die Hochachse, in der unsere Kette rechnet: Blenders Weltsystem, Z oben.
#:
#: Nach dem glTF-Import steht die Szene IMMER Z-up da — bei einer Y-up-Datei durch
#: Blenders eigene Umrechnung ``R_x(+90)``, bei einer Z-up-Datei, weil der Runner sie
#: mit ``--rotiere-z-up`` wieder zurückdreht. Ein Standort in dieser Achse braucht
#: darum keine Drehung mehr, ein Y-up-Standort genau eine.
HOCHACHSE_BLENDER = "z"

#: Die Hochachse der glTF-Konvention. `CameraSpec.up_axis` erlaubt genau diese beiden.
HOCHACHSE_GLTF = "y"


def kamera_nach_blender(punkt, up_axis):
    """Ein Kamerapunkt aus einer ``CameraSpec`` → Blenders Weltsystem.

    **Der Anlass ist Demolauf 12** (01.09.2026). Der Auto-Kamera-Knoten schickte eine
    fertige Kameraliste mit ``up_axis: "y"``; die Geometrie wurde beim Import gedreht,
    die Kamera nicht. Gemessen an der glb dieses Auftrags::

        Szenenbox in Blender   x  68.513 … 173.963   y 60.482 … 119.692   z −0.985 … 29.314
        Auge, wie gestellt     (121.238,   0.615, 23.878)   → y liegt 59,9 m NEBEN dem Bau
        Blickziel, wie gestellt (121.238, 11.135, −90.087)  → z liegt 89,1 m UNTER dem Bau
        Blickziel, gedreht     (121.238, 90.087,  11.135)   → x und y exakt die Boxmitte

    Dass das gedrehte Blickziel beider Kameras **genau** auf der Mitte der Szenenbox
    landet, ist der Beleg: Die Liste war in Dateikoordinaten gerechnet, und es fehlte
    genau diese eine Drehung.

    ``up_axis`` ist in ihrem Vertrag **Pflichtfeld ohne Vorgabewert** — ausdrücklich
    wegen eines früheren Vorfalls (P-ACHSENRIEGEL). Es wurde gesendet, für die
    Geometrie angewandt und für die Kamera **verworfen**: :func:`spec_zu_kamera` las
    ``position``, ``target``, ``name`` und ``fov``, und sonst nichts.

    Args:
        punkt: drei Zahlen in der Achse ``up_axis``.
        up_axis: ``"y"`` (glTF) oder ``"z"`` (CAD/Blender). Gross-/Kleinschreibung egal.

    Returns:
        Der Punkt in Blenders Weltsystem — bei ``"z"`` unverändert, bei ``"y"`` um
        ``R_x(+90)`` gedreht, also mit **derselben** Rechnung, die
        :func:`aiimaging.contracts.blender_gltf_import_dreht` für die Geometrie
        ausschreibt. Eine zweite Fassung dieser Formel wäre die Falle noch einmal.

    Raises:
        SzenenError: ``up_axis`` fehlt oder ist weder ``y`` noch ``z``. **Es wird nicht
            geraten** — genau dafür steht das Pflichtfeld im fremden Vertrag, und ein
            Vorgabewert hier wäre die stille Verdrehung, gegen die er gebaut wurde.
            Ebenso, wenn ``punkt`` keine drei endlichen Zahlen trägt (seit der Runde 8)
            — ``True`` und ``'5'`` zählen seit der Runde 9 nicht als Zahlen.
    """
    achse = _hochachse(up_axis)
    # Die Funktion ist oeffentlich und sagt `SzenenError` zu; `spec_zu_kamera` prueft
    # vorher selbst, andere Aufrufer nicht. Befunde, die hier einzeln geflickt wurden:
    # ein Text warf nackt (Durchsicht 23.09.2026), eine ganze Zahl mit 400 Stellen
    # OverflowError (Runde 7c), `[inf, 0, 0]` kam als `(inf, 0.0, 0.0)` zurueck (Runde 8),
    # `[True, '5', 0]` als `(1.0, 5.0, 0.0)` und `[1, 2]` ohne Einwand als Paar (Runde 9).
    # Seither die eine Pruefung `_lies_kamerapunkt`.
    zahlen = _lies_kamerapunkt(punkt, "Kamerapunkt", "punkt")
    if achse == HOCHACHSE_BLENDER:
        return tuple(zahlen)
    return tuple(_contracts.blender_gltf_import_dreht(zahlen))


def _hochachse(wert) -> str:
    """``up_axis`` einer ``CameraSpec`` prüfen — ohne Vorgabewert."""
    if wert is None:
        raise SzenenError(
            "CameraSpec ohne 'up_axis'. Das Feld ist in `kosmovis.render-scene/v1` "
            "PFLICHT und hat KEINEN Vorgabewert (P-ACHSENRIEGEL, 26.08.2026) — "
            "`position` und `target` sind ohne es mehrdeutig, und beide Deutungen "
            "sehen wie brauchbare Zahlen aus. Wer hier eine Achse annimmt, wiederholt "
            "Demolauf 12: Geometrie gedreht, Kamera nicht, Tiefenbild ohne einen "
            "einzigen Geometriepixel."
        )
    achse = str(wert).strip().lower()
    if achse in (HOCHACHSE_BLENDER, HOCHACHSE_GLTF):
        return achse
    raise SzenenError(
        f"CameraSpec 'up_axis' ist {wert!r}. Ihr Vertrag lässt genau {HOCHACHSE_GLTF!r} "
        f"und {HOCHACHSE_BLENDER!r} zu; auf einen der beiden zu raten hiesse, eine "
        f"90-Grad-Drehung zu würfeln."
    )


def spec_zu_kamera(spec: dict) -> dict:
    """Fremde ``CameraSpec`` → unsere Kamerafelder, **in Blenders Weltsystem**.

    Die Gegenrichtung zu :func:`kamera_zu_spec`. Seit dem 01.09.2026 wird dabei
    ``up_axis`` gelesen und angewandt — siehe :func:`kamera_nach_blender` für den
    Vorfall, der das erzwingt.

    Returns:
        ``{kuerzel, auge, blick_auf, brennweite_mm, up_axis, auge_bestellt,
        blick_auf_bestellt}``. Die beiden ``…_bestellt``-Felder tragen die Zahlen, wie
        sie hereinkamen: Ohne sie wäre eine gedrehte Kamera von einer ungedrehten im
        Bericht nicht mehr zu unterscheiden, und genau diese Unterscheidung hat vier
        Tage gekostet.

    Raises:
        SzenenError: ``position`` oder ``target`` fehlen oder sind keine drei endlichen
            Zahlen (``true`` und ``"5"`` zählen seit der Runde 9 nicht) — oder
            ``up_axis`` fehlt (Pflichtfeld ohne Vorgabewert).
    """
    if not isinstance(spec, dict):
        raise SzenenError(f"CameraSpec ist kein Wörterbuch: {spec!r}")
    achse = _hochachse(spec.get("up_axis"))
    werte = {}
    for fremd, unser in (("position", "auge"), ("target", "blick_auf")):
        # Die eine Pruefung `_lies_kamerapunkt` (Runde 9, 23.09.2026). Sie haelt, was
        # hier einzeln geflickt war — `Infinity` aus dem Python-JSON (23.09.2026), eine
        # ganze Zahl mit 400 Stellen (Runde 7c) — und weist seither auch `true` und
        # `"5"` ab, die `float` still zu 1.0 und 5.0 machte. Die Form (drei Eintraege)
        # wurde mit `repr` der ganzen Liste gemeldet, und das warf bei einer riesigen
        # Zahl selbst.
        bestellt = _lies_kamerapunkt(spec.get(fremd), f"CameraSpec '{fremd}'", fremd)
        werte[unser] = kamera_nach_blender(bestellt, achse)
        werte[f"{unser}_bestellt"] = bestellt
    werte["kuerzel"] = spec.get("name")
    werte["brennweite_mm"] = fov_zu_brennweite(spec.get("fov", 50.0))
    werte["up_axis"] = achse
    # Gelesen und berichtet, nicht angewandt — siehe KAMERA_FELDER.
    bezug = spec.get("referenzpunkt")
    if bezug is not None and bezug not in KAMERA_REFERENZPUNKTE:
        raise SzenenError(
            f"CameraSpec 'referenzpunkt' ist {bezug!r}. Ihr Vertrag kennt "
            f"{', '.join(KAMERA_REFERENZPUNKTE)}; ein anderer Wert hiesse, dass die "
            f"Augenhöhe auf etwas bezogen ist, das wir nicht kennen.")
    werte["referenzpunkt"] = bezug
    # DIE PERSPEKTIVE (Entscheid 109, 20.10.2026): 'senkrecht' heisst waagrechte Achse mit
    # Objektiv-Shift (abholer rechnet ihn ueber `kameras.shift_aus_ziel`), 'frei' gekippt.
    # Fehlt sie, bleibt alles wie bisher (gekippt, das Ziel wie bestellt).
    perspektive = spec.get("perspektive")
    if perspektive is not None and perspektive not in PERSPEKTIVEN:
        raise SzenenError(
            f"CameraSpec 'perspektive' ist {perspektive!r}. Erwartet ist 'senkrecht' oder "
            f"'frei' (oder das Feld weglassen).")
    werte["perspektive"] = perspektive
    return werte


# --------------------------------------------------------------------------------------
# Backbone
# --------------------------------------------------------------------------------------

def backbone_von_fremd(fremd: str) -> dict:
    """Ihr Backbone-Kürzel → unser Registry-Name, oder eine Begründung.

    Returns:
        ``{name, bekannt, zulaessig, begruendung}``. ``name`` ist ``None``, wenn wir
        keinen Eintrag haben — dann wird **nicht** auf die Vorgabe zurückgefallen. Ein
        stillschweigend ersetztes Modell wäre ein anderes Bild unter demselben Auftrag.
    """
    unser = BACKBONE_VON_FREMD.get(fremd)
    if unser is None:
        return {"name": None, "bekannt": False, "zulaessig": False,
                "begruendung": (
                    f"Das fremde Backbone-Kürzel {fremd!r} hat bei uns keine Entsprechung. "
                    f"Bekannt sind: {', '.join(sorted(BACKBONE_VON_FREMD))}. Es wird NICHT "
                    f"auf die Vorgabe zurückgefallen — ein stillschweigend ersetztes "
                    f"Modell wäre ein anderes Bild unter demselben Auftrag.")}
    # `ladefreigabe`, nicht `pruefe_lizenz`: Ein Eintrag mit offener Lizenz (E128) ist
    # bestellbar, obwohl er nicht verkaufbar ist. Fuer alle anderen dieselbe Antwort.
    urteil = _backbone.ladefreigabe(unser, umgebung={})
    return {"name": unser, "bekannt": True, "zulaessig": urteil["darf"],
            "begruendung": urteil["begruendung"]}


def backbone_nach_fremd(unser: str) -> dict:
    """Unser Registry-Name → ihr Kürzel, oder eine benannte Lücke.

    **Unser Vorgabe-Backbone lässt sich dort nicht ausdrücken.** Ihre Liste führt
    ``qwen``, ``flux2-klein``, ``flux-krea``, ``sdxl``; `z-image-turbo` steht nicht
    darin. Von den vieren ist genau einer unter Regel 1 ausgeschlossen — ``flux-krea``;
    ``flux2-klein`` ist entgegen dem ersten Anschein Apache-2.0.

    Returns:
        ``{kuerzel, ausdrueckbar, begruendung}``. ``kuerzel`` ist ``None``, wenn es
        keines gibt — dann muss der Aufrufer entscheiden, nicht dieses Modul.
    """
    rueck = {v: k for k, v in BACKBONE_VON_FREMD.items()}
    kuerzel = rueck.get(unser)
    if kuerzel is not None:
        return {"kuerzel": kuerzel, "ausdrueckbar": True,
                "begruendung": f"{unser} entspricht dort {kuerzel!r}."}
    return {"kuerzel": None, "ausdrueckbar": False, "begruendung": (
        f"{unser!r} lässt sich im fremden Vertrag NICHT ausdrücken — seine Liste kennt "
        f"nur {', '.join(FREMDE_BACKBONES)}. Das betrifft ausgerechnet unseren "
        f"Vorgabe-Backbone: Er ist Apache-2.0 und am Gerät gemessen (auf-20260818-13), "
        f"und er hält die Geometrie, wo der dort vorgegebene 'qwen' sie verliert "
        f"(spearman -0.853 gegen +0.005). Die Lücke gehört gemeldet, nicht überbrückt — "
        f"ein stillschweigend ersetztes Modell wäre ein anderes Bild unter demselben "
        f"Auftrag.")}


# --------------------------------------------------------------------------------------
# Ihre Szene lesen
# --------------------------------------------------------------------------------------

#: Vielfaches, auf das Bildbreite und -höhe fallen müssen.
#:
#: **Am Gerät gefunden (Demolauf 3, 19.08.2026):** Der fremde Vertrag verlangt
#: standardmässig 1600 × 1000. 1600 ist durch 16 teilbar, 1000 nicht (62,5) — und die
#: Pipeline weist das ab::
#:
#:     ValueError: Height must be divisible by 16 (got 1000)
#:
#: Der Grund liegt im Bauplan latenter Diffusionsmodelle: Der VAE verkleinert um 8, der
#: Transformer arbeitet auf 2×2-Kacheln. 16 ist das Produkt, keine Marotte.
RASTER = 16


def _auf_raster(aufl):
    """Bildmasse auf ein Vielfaches von :data:`RASTER` bringen — **und es sagen**.

    Gerundet wird **abwärts**: Ein grösseres Bild als bestellt wäre eine stille
    Erweiterung des Ausschnitts, ein kleineres ist ein sichtbarer Beschnitt. Wer den
    Unterschied kennt, kann ihn ausgleichen; wer ihn nicht gesagt bekommt, sucht später
    einen Massstabsfehler.

    Returns:
        ``(masse, hinweis)``. ``hinweis`` ist ``""``, wenn nichts zu tun war.
    """
    b, h = int(aufl[0]), int(aufl[1])
    nb, nh = max(RASTER, b - b % RASTER), max(RASTER, h - h % RASTER)
    if (nb, nh) == (b, h):
        return [b, h], ""
    return [nb, nh], (
        f"Bildmasse {b}x{h} auf {nb}x{nh} gebracht: Breite und Höhe müssen Vielfache von "
        f"{RASTER} sein, sonst weist die Pipeline den Lauf ab (Demolauf 3: 'Height must "
        f"be divisible by 16 (got 1000)'). Abgerundet, nicht aufgerundet — ein grösseres "
        f"Bild wäre eine stille Erweiterung des Ausschnitts. Das Seitenverhältnis "
        f"verschiebt sich dabei von {b/h:.4f} auf {nb/nh:.4f}; wer die Kamera daran "
        f"kalibriert hat, rechnet mit diesem Wert."
    )


def _ki_raster_hinweis(aufl) -> str:
    """Der Satz, wenn die bestellte Grösse nicht auf das Raster fällt — ``""`` sonst.

    Seit auf-20261020-292 (Befund B5) bleibt die Grösse **wie bestellt**: Blender rechnet sie,
    die Prüfung misst auf ihr, und das Ergebnis hat sie. Nur der KI-Schritt rechnet auf
    :func:`_auf_raster` gerundet und wird danach auf die bestellte Grösse zurückgebracht.
    """
    (nb, nh), roh = _auf_raster(aufl)
    if not roh:
        return ""
    b, h = int(aufl[0]), int(aufl[1])
    return (f"Bildmasse {b}x{h} bleiben, wie bestellt: Blender rechnet {b}x{h}, und das "
            f"Ergebnis hat diese Grösse. Nur der KI-Schritt rechnet intern {b}x{h} auf "
            f"{nb}x{nh} (Vielfache von {RASTER}, sonst weist die Pipeline ab) — oder grösser, "
            f"wenn das Modell eine Untergrenze hat (auf-20261020-293) — und bringt "
            f"sein Bild danach auf {b}x{h} zurück; das Seitenverhältnis der Kamera bleibt "
            f"{b/h:.4f}.")


#: Welche Felder der fremden Bestellung wir **lesen** — je Block.
#:
#: **Warum es diese Karte gibt** (HomeStation, 11.09.2026, und der Cloud-Worker hat
#: dieselbe Lücke unabhängig auf seiner Seite gefunden):
#:
#:     `lies_szene` liest feldweise mit ``.get()`` und prüft **nicht** auf unbekannte
#:     Felder. Ein neues ``qualitaet: "FINAL"`` käme also an und würde verschluckt — der
#:     Besteller hält das Bild für das bestellte.
#:
#: Am 11.09.2026 hier nachgemessen und bestätigt: Drei erfundene Felder gehen hinein,
#: ``maengel`` bleibt leer, ``stehengebliebene_felder`` bleibt leer, keines taucht wieder
#: auf. **Und die Lage war schärfer als gemeldet:** Wir hatten den Melder längst
#: (:data:`STEHENGEBLIEBEN`) — er kannte genau drei **bekannte** Felder. *Ein Wächter, der
#: nur kennt, was man ihm genannt hat, fängt keine Neuigkeit.*
#:
#: Die HomeStation hat die Regel dazu aus ihrem Renderprojekt mitgeschickt, und sie ist
#: der Grund für die Form dieser Karte: **Ein Riegel prüft, ob jedes Element der
#: WIRKLICHKEIT in seiner Liste steht — nicht, ob jedes Element seiner Liste in der
#: Wirklichkeit vorkommt. Der zweite besteht immer.**
#:
#: **Seit dem 22.09.2026 heisst «bekannt» nicht mehr «gelesen».** Die Antwort auf
#: ``auf-20260911-104`` nannte neun Felder ihrer ``render-scene``, die hier fehlten — und
#: eines davon, ``interior``, wird seit dem 19.09.2026 wirklich gesendet. Unser Riegel
#: wies damit **jede** Innenraum-Bestellung ab. Zwei der neun bedienen wir seither
#: (``interior``, ``gelaende``); die übrigen sieben stehen in :data:`ABGEWIESENE_FELDER`
#: und werden **mit ihrem eigenen Satz** abgewiesen statt als «unbekannt». Abweisen bleibt
#: der Grundsatz (E75 drüben, 19.09.2026) — nur sagt die Abweisung jetzt, *warum*.
BEKANNTE_FELDER = {
    "": ("schema", "geometry", "render", "style", "vis", "cameras", "out",
         "interior", "gelaende", "komposition", "innenansichten", "context", "skizze",
         "cameras_auto"),
    "geometry": ("path", "format", "up_axis"),
    "render": ("resolution", "faithful", "samples", "sun",
               "environment", "himmel", "belichtung", "rauschschwelle", "passes",
               "materialien"),
    "style": ("prompt", "mode", "refs"),
    "vis": ("backbone", "skip", "upscale", "research_only", "grundlage", "seed", "guete",
            # Seit 21.10.2026 (auf-20261021-296, N3): unser Messschalter, NICHT im Vertrag
            # drüben — siehe `ZUSATZ_LEERER_HINTERGRUND`. Vorgabe aus.
            "leerer_hintergrund",
            # Seit 21.10.2026 (Entscheid 117, auf-20261021-298): zwei weitere Messschalter
            # von uns, NICHT im Vertrag — siehe `lies_farbabgleich` und `lies_bildeingang`.
            "farbabgleich", "bildeingang",
            # Seit 21.10.2026 (Strang Treue, Planblatt Material und Umriss): zwei weitere
            # Messschalter, NICHT im Vertrag — `lies_umriss_halten`, `lies_material_vorne`.
            "umriss_halten", "material_vorne", "himmel_sichtbar",
            # Seit 23.10.2026 (Mac-Befund «haus-am-hang», auf-20261023-346): zwei weitere
            # Messschalter, NICHT im Vertrag — `lies_glas_satz`, `lies_material_vorne_nennungen`.
            "glas_satz", "material_vorne_nennungen",
            # Seit 24.10.2026 (Knoten «Umfeld», Owner-Wunsch): Baeume, Bueche, Wiese, Strasse,
            # Autos um das Haus — gelesen in `umfeld.lies_wunsch`, gestellt in Blender.
            "umfeld",
            # Seit 24.10.2026 (Entscheid 149): das bewusst freie Bild — ohne Grundbild als Start,
            # ohne «Umriss halten», gekennzeichnet bis ins Ergebnis. `lies_freies_bild`.
            "freies_bild",
            # Seit 25.10.2026 (Mac-Probe 0.3.66, KosmoVis-Zweig `claude/kosmovis-macweg`): der
            # Auftrag ist eine Variante — Staerke 0,7 auch ohne `grundlage`. `lies_variante`.
            "variante"),
    # Belegt ist genau EIN Unterfeld (auf-31 R3, auf-91 V1): `rooms`, gesendet als
    # "auto". Ein `view` (frontal/ueber Eck) ist drueben ausdruecklich NICHT gebaut —
    # kaeme es trotzdem, faellt es hier als unbekannt auf und nicht still weg.
    "interior": ("rooms",),
    # Seit 08.10.2026 (Owner-Entscheid 76, Feldnamen vom Integrator): die Umgebung als
    # Splat. Gelesen in `kontext_aus_szene`.
    "context": ("kind", "ply", "verortung", "transform", "fit", "crs_note"),
    # Seit 15.10.2026 (Owner-Entscheid 96): die Skizze vom iPad fuehrt das Bild. Gelesen in
    # `skizze_aus_szene`, gerechnet in `abholer` ueber `arbeitsgang.rechne_skizze`.
    "skizze": ("quelle", "name", "anweisung"),
    # Seit 20.10.2026 (Entscheide 109/113, Vertrag mit dem Integrator): die Auto-Kamera mit
    # ihren Parametern. Gelesen in `kameras_auto_aus_szene`; `abstand` prueft sie selbst.
    "cameras_auto": ("richtungen", "augenhoehe_m", "brennweite_mm", "abstand", "perspektive"),
}

#: Die Unterfelder von ``render.environment`` (Entscheid 110, Vertrag 20.10.2026) — geprueft
#: in :func:`umgebung_aus_szene`, nicht in :func:`unbekannte_felder` (zwei Ebenen tief).
UMGEBUNG_FELDER = ("preset", "hdri", "intensitaet", "rotationGrad")

#: Der einzige belegte Inhalt von ``interior.rooms``: seit dem 19.09.2026 gesendet, je
#: Auftrag genau EIN Innenstandpunkt (auf-31 R3, auf-91 V5).
INTERIOR_ROOMS_AUTO = "auto"

#: Felder, die wir aus ihrem Vertrag **kennen** und trotzdem abweisen — je mit dem Satz,
#: der der Gegenseite sagt, warum (Antwort auf ``auf-20260911-104``, V2: «die sechs
#: Felder aufnehmen oder je Feld ablehnen»).
#:
#: Warum abweisen und nicht als «bekannt, nicht bedient» durchlassen: Keines davon liest
#: unsere Kette, und bei fünf von sieben ist nicht einmal belegt, was sie verlangen. Ein
#: Lauf, der sie still übergeht, liefert ein Bild, das nach Bestellung aussieht und keine
#: ist — genau der Fall, gegen den die Karte gebaut ist. Ein Feld, das ``null`` trägt,
#: verlangt nichts und wird **nicht** abgewiesen (dieselbe Regel wie :func:`wert_oder`).
ABGEWIESENE_FELDER = {
    "komposition": (
        "Bekannt (seitenverhaeltnis, brennweiteMm, horizontlinie), aber von unserer "
        "Kette nicht gelesen. Die Brennweite steht schon in den Kameras (fov), das "
        "Seitenverhaeltnis in render.resolution, und was horizontlinie misst, ist nicht "
        "belegt. Noetig waere: die Deutung von horizontlinie und eine Regel, welche "
        "Angabe gilt, wenn Kamera und komposition sich widersprechen."),
    "innenansichten": (
        "Bei euch ein geduldeter Zweitname von 'interior' (auf-31 R3), gesendet wird er "
        "nicht (auf-104, Stand 19.09.2026). Angenommen wird nur 'interior' — zwei Namen "
        "fuer dieselbe Bestellung sind zwei Stellen, an denen sie sich widersprechen kann."),
    # `render.environment` stand hier bis zum 20.10.2026 («ein bestelltes Umgebungslicht
    # fiele still weg»). Seit Entscheid 107 (CC0-Himmelsbilder am Heim-PC) wird es gelesen:
    # `umgebung_aus_szene`, gerechnet im Runner (`--umgebung-hdr`).
    "render.himmel": (
        "Form bekannt (render-scene.ts: modell, staerke, luftdichte, aerosoldichte, "
        "drehungGrad), aber unsere Kette liest das Feld nicht: Der Himmel unseres "
        "Cycles-Schritts ist fest, und das KI-Bild entsteht aus der Tiefe, nicht aus dem "
        "Himmel. Noetig waere eine Leitung bis in den Blender-Schritt (B161, 24.09.2026)."),
    "render.belichtung": (
        "Form bekannt (render-scene.ts: belichtung, farbraum, anmutung), aber unsere "
        "Kette liest das Feld nicht: Die Farbverwaltung unseres Cycles-Schritts ist fest. "
        "Noetig waere eine Leitung bis in den Blender-Schritt (B161, 24.09.2026)."),
    "render.rauschschwelle": (
        "Form bekannt (render-scene.ts: Zahl 0..1, Cycles adaptive_threshold), aber "
        "unsere Kette liest das Feld nicht: Die Abtastung unseres Cycles-Schritts steuert "
        "render.samples allein. Noetig waere eine Leitung bis in den Blender-Schritt "
        "(B161, 24.09.2026)."),
    "vis.research_only": (
        "Der Name ist bekannt (auf-104), die Bedeutung nicht. Gaebe es Modelle mit "
        "reiner Forschungslizenz frei, widerspraeche es Regel 1 (nur permissive "
        "Lizenzen); kennzeichnete es nur das Bild, fehlt der Ort, an dem es ankaeme. Wir "
        "raten nicht, welches von beiden gemeint ist."),
}


def abgewiesene_felder(fremd: dict) -> tuple[str, ...]:
    """Je gesetztem Feld aus :data:`ABGEWIESENE_FELDER` ein Satz — leer, wenn keines da ist.

    «Gesetzt» heisst: vorhanden **und nicht** ``null``. Ein ausdrückliches ``null``
    verlangt nichts; es abzuweisen hiesse, eine Bestellung für ein Feld abzulehnen, das
    sie gar nicht benutzt.
    """
    if not isinstance(fremd, dict):
        raise SzenenError(f"render-scene ist kein Wörterbuch: {type(fremd).__name__}")
    saetze = []
    for pfad, grund in ABGEWIESENE_FELDER.items():
        block, _, name = pfad.rpartition(".")
        quelle = fremd.get(block) if block else fremd
        if not isinstance(quelle, dict) or quelle.get(name) is None:
            continue
        saetze.append(
            f"Feld '{pfad}' ({quelle[name]!r}) wird abgewiesen: {grund} Abgewiesen statt "
            f"uebergangen (E75 drueben, 19.09.2026): Wer ein Feld setzt und kein Wort "
            f"hoert, haelt es fuer bedient.")
    return tuple(saetze)

#: Blöcke, deren Inhalt **nicht** durchsucht wird, mit dem Grund.
#:
#: ``render.sun`` reichen wir unverändert an den Runner weiter — was darin steht, ist
#: seine Sache, und eine Prüfung hier würde eine Zuständigkeit erfinden. ``cameras`` ist
#: entweder ``"auto"`` oder eine Liste von Kameraspezifikationen; deren Schlüssel prüft
#: seit dem 24.09.2026 :data:`KAMERA_FELDER` (unten, in :func:`unbekannte_felder`).
NICHT_DURCHSUCHT = ("render.sun", "cameras")

#: Die Schlüssel einer ``CameraSpec``, die wir kennen (B161/B3, 24.09.2026).
#:
#: **Bis dahin wurde eine Kameraliste gar nicht auf fremde Schlüssel geprüft** — ein
#: ``referenzpunkt`` kam an und fiel wortlos weg, und jedes neue Feld hätte es ebenso
#: getan. ``referenzpunkt`` verlangt nichts: Er sagt, auf welche Höhe sich die Augenhöhe
#: drüben bezog (``okff``, ``huellbox_unterkante``, ``weltnull``); ``position`` trägt die
#: Zahl bereits im Weltsystem. Er wird darum gelesen und in den Bericht getragen, nicht
#: angewandt.
KAMERA_FELDER = ("name", "position", "target", "fov", "up_axis", "referenzpunkt",
                 # Seit 20.10.2026 (Entscheid 109): 'senkrecht' (Shift, waagrechte Achse)
                 # oder 'frei' (gekippt wie bisher). Fehlt es, bleibt alles wie bisher.
                 "perspektive")

#: Die beiden Werte von ``perspektive`` (CameraSpec und ``cameras_auto``).
PERSPEKTIVE_SENKRECHT = "senkrecht"
PERSPEKTIVE_FREI = "frei"
PERSPEKTIVEN = (PERSPEKTIVE_SENKRECHT, PERSPEKTIVE_FREI)

#: Die Schlüssel von ``render.sun``, die wir kennen — und seit dem 24.09.2026 auch prüfen.
#:
#: Bis dahin stand ``render.sun`` in :data:`NICHT_DURCHSUCHT` mit dem Grund, eine Prüfung
#: hier «erfände eine Zuständigkeit». Gemessen zu B161: ``staerke``, ``kelvin`` und
#: ``winkelGrad`` kamen an, fielen wortlos weg — und die Warnung sagte «Sonnenstand … wird
#: bedient». Ein Tippfehler (``azimut`` statt ``azimuth``) fiel still auf die Vorgabe
#: zurück. Seither werden alle fünf gelesen und bis in den Blender-Schritt gereicht.
SONNE_FELDER = ("azimuth", "elevation", "staerke", "kelvin", "winkelGrad")
KAMERA_REFERENZPUNKTE = ("okff", "huellbox_unterkante", "weltnull")


def unbekannte_felder(fremd: dict) -> tuple[str, ...]:
    """Welche Felder dieser Bestellung wir **gar nicht kennen** — mit Punktpfad.

    Unterschieden wird von :func:`stehengebliebene_felder`, und der Unterschied ist der
    ganze Punkt:

    ========================  ===================================================
    :func:`stehengebliebene_felder`  Wir **kennen** das Feld und bedienen es nicht.
    :func:`unbekannte_felder`        Wir kennen es **nicht** — es kann alles heissen.
    ========================  ===================================================

    Das erste ist eine bekannte Lücke mit einem Grund. Das zweite ist eine Bestellung,
    die wir nicht verstanden haben — und die niemandem auffällt, wenn sie durchrutscht.

    Returns:
        Punktpfade in der Reihenfolge der Karte, dann alphabetisch. Leer, wenn alles
        bekannt ist.
    """
    if not isinstance(fremd, dict):
        raise SzenenError(f"render-scene ist kein Wörterbuch: {type(fremd).__name__}")

    gefunden: list[str] = []
    for block, bekannt in BEKANNTE_FELDER.items():
        if block == "":
            inhalt = fremd
        else:
            if block in NICHT_DURCHSUCHT:
                continue
            inhalt = fremd.get(block)
            if not isinstance(inhalt, dict):
                continue          # fehlt, oder ist kein Block — beides nicht hier zu melden
        for name in sorted(inhalt):
            pfad = f"{block}.{name}" if block else str(name)
            if pfad in NICHT_DURCHSUCHT:
                continue
            if name not in bekannt:
                gefunden.append(pfad)
    render_block = fremd.get("render")
    sonne_block = render_block.get("sun") if isinstance(render_block, dict) else None
    if isinstance(sonne_block, dict):
        gefunden.extend(f"render.sun.{name}" for name in sorted(sonne_block)
                        if name not in SONNE_FELDER)
    kameras = fremd.get("cameras")
    if isinstance(kameras, list):
        for i, spec in enumerate(kameras):
            if isinstance(spec, dict):
                gefunden.extend(f"cameras[{i}].{name}" for name in sorted(spec)
                                if name not in KAMERA_FELDER)
    return tuple(gefunden)


#: Die Arten von ``context.kind``, die wir rendern können. Heute nur der Splat.
KONTEXT_ARTEN = ("splat",)

#: Die Werte von ``context.fit`` — wie die Lage des Splats zustande kam (Integrator,
#: 08.10.2026): ``behelf`` von Hand gesetzt, ``passpunkte`` über Passpunkte eingepasst.
KONTEXT_FIT = ("behelf", "passpunkte")

#: Der Satz zu ``fit: behelf``, wörtlich wie bestellt — er geht in ``verdict.hinweise``.
SATZ_KONTEXT_BEHELF = "Lage des Splats von Hand gesetzt, nicht vermessen."

#: Der Massstab des Splats aus ``splat.verortung.json`` (KosmoPrepare, 14.10.2026): Ampel und
#: was sie sagt. KosmoPrepare setzt die Ampel (aus Unsicherheit der IMU und Abweichung der
#: Tiefen-Gegenprobe); Visbox **übernimmt sie, entscheidet sie nicht** — und sagt sie im Urteil.
MASSSTAB_AMPELN = {"gruen": "gruen", "grün": "gruen", "gelb": "gelb", "rot": "rot"}

#: Ab dieser Drift entlang des Wegs ein eigener Satz (KosmoPrepare: «Zusatzhinweis, wenn s
#: entlang des Wegs um mehr als 10 % driftet»).
MASSSTAB_DRIFT_SATZ_AB = 0.10


def _prozent(wert) -> str | None:
    if isinstance(wert, bool) or not isinstance(wert, (int, float)):
        return None
    return f"{abs(float(wert)) * 100:.0f} %"


def massstab_aus_verortung(pfad) -> tuple[dict | None, list[str]]:
    """Der Block ``massstab`` aus der Verortungsdatei des Splats → ``(vermerk, saetze)``.

    **Nur zur Auskunft, nie zum Rechnen:** Die Lage samt Massstab steht in
    ``context.transform``; dieser Block sagt, **wie verlässlich** der Massstab ist. Darum ist
    nichts davon ein Mangel: Fehlt die Datei oder der Block, gibt es keinen Satz (ältere
    Verortungen kennen ihn nicht); ist sie nicht lesbar, ein Satz, der das sagt.

    Sätze je Ampel (KosmoPrepare setzt sie, Visbox übernimmt): **grün** nennt Wert und
    Unsicherheit; **gelb** sagt «unsicher» mit den Gründen und dass ein Kontrollmass ihn
    sichern würde; **rot** sagt «nicht verlässlich», der Behelf bleibt. ``herkunft: "hand"``
    (ein Handmass gewinnt immer) sagt nur, dass von Hand gemessen ist. Dazu ein Satz, wenn
    ``drift_rel`` über :data:`MASSSTAB_DRIFT_SATZ_AB` liegt.

    Returns:
        ``vermerk`` — ``{wert, einheit, unsicherheit_rel, herkunft, ampel, gegenprobe_rel,
        drift_rel}`` (nur Zahlen und Wörter, kein Pfad) oder ``None``; ``saetze`` für
        ``verdict.hinweise``.
    """
    import json as _json                                     # noqa: PLC0415
    from pathlib import Path

    p = Path(pfad)
    if not p.is_file():
        return None, []
    try:
        roh = _json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, [f"KONTEXT, Massstab: Die Verortung {p.name!r} ist nicht lesbar — wie "
                      f"verlaesslich der Massstab ist, bleibt offen."]
    block = roh.get("massstab") if isinstance(roh, dict) else None
    if block is None:
        return None, []
    if not isinstance(block, dict):
        return None, ["KONTEXT, Massstab: Der Block 'massstab' der Verortung ist kein Block — "
                      "wie verlaesslich der Massstab ist, bleibt offen."]
    wert = block.get("wert")
    zahl = (isinstance(wert, (int, float)) and not isinstance(wert, bool)) and wert > 0
    gegen = block.get("gegenprobe") if isinstance(block.get("gegenprobe"), dict) else {}
    ampel = MASSSTAB_AMPELN.get(str(block.get("ampel") or "").strip().lower())
    herkunft = block.get("herkunft") if isinstance(block.get("herkunft"), str) else None
    vermerk = {"wert": float(wert) if zahl else None, "einheit": block.get("einheit"),
               "unsicherheit_rel": block.get("unsicherheit_rel"), "herkunft": herkunft,
               "ampel": ampel, "gegenprobe_rel": gegen.get("abweichung_rel"),
               "drift_rel": block.get("drift_rel")}
    mass = f"{float(wert):.2f} m je Modelleinheit" if zahl else "ohne lesbaren Wert"
    plusminus = _prozent(block.get("unsicherheit_rel"))
    mass_mit = mass + (f", ± {plusminus}" if plusminus and zahl else "")
    gruende = [g for g in (block.get("gruende") or ()) if isinstance(g, str) and g.strip()]
    warum = (" (" + "; ".join(" ".join(g.split()) for g in gruende) + ")") if gruende else ""
    woher = {"imu": "aus der Bewegung der Kamera (IMU)"}.get(herkunft or "",
                                                           f"aus {herkunft}" if herkunft else
                                                           "ohne Herkunft")
    saetze = []
    if herkunft == "hand":
        saetze.append(f"KONTEXT, Massstab von Hand gemessen: {mass}.")
    elif ampel == "gruen":
        saetze.append(f"KONTEXT, Massstab {woher}: {mass_mit}.")
    elif ampel == "gelb":
        saetze.append(f"KONTEXT, Massstab UNSICHER{warum}: {mass_mit} {woher} — ein "
                      f"Kontrollmass am Bau wuerde ihn sichern.")
    elif ampel == "rot":
        saetze.append(f"KONTEXT, Massstab NICHT VERLAESSLICH{warum}: Der Behelf bleibt; ein "
                      f"Kontrollmass am Bau fehlt.")
    else:
        saetze.append(f"KONTEXT, Massstab {woher}: {mass_mit} — ohne bekannte Ampel "
                      f"({block.get('ampel')!r}), also nicht beurteilt.")
    drift = block.get("drift_rel")
    if (isinstance(drift, (int, float)) and not isinstance(drift, bool)
            and abs(drift) > MASSSTAB_DRIFT_SATZ_AB):
        saetze.append(f"KONTEXT, Massstab aendert sich entlang des Wegs um {_prozent(drift)} — "
                      f"Masse weit vom Start der Aufnahme weichen ab.")
    return vermerk, saetze


#: Der Schluessel, unter dem ein **Kameraurteil** den Kontext dieses Laufs vermerkt —
#: :func:`kontext_vermerk` oder ``None`` (gesetzt in ``abholer.verarbeiter``).
URTEIL_KONTEXT = "kontext"


def kontext_aus_szene(roh) -> dict | None:
    """``RenderScene.context`` → was der Multipass als Umgebung bekommt — oder ``None``.

    **Owner-Entscheid 76 (08.10.2026):** Der Splat läuft als Umgebung im Multipass mit,
    gemessen wird weiter nur das Bauwerk (siehe :mod:`aiimaging.kontext`). Die Form kommt
    vom Integrator: ``{kind: "splat", ply: <absoluter Pfad auf der HomeStation>,
    verortung: <Pfad> | null, transform: [16], fit: "behelf" | "passpunkte",
    crs_note: <Satz>}``.

    **Ein unbrauchbarer Kontext ist ein MANGEL, kein leerer.** Unbekannte Art, fehlende
    Datei, eine Matrix, die keine ist: Der Lauf wird angehalten und der Grund steht im
    Ergebnis. Ohne Umgebung zu rendern sähe aus wie ein Bild mit — die bestellende Seite
    hielte die Umgebung für geliefert.

    Returns:
        ``None``, wenn ``context`` fehlt oder ``null`` ist (nicht bestellt). Sonst
        ``{art, ply, datei, matrix, fit, crs_note, verortung, massstab, hinweise, maengel}`` —
        ``ply`` ist der Pfad für den Multipass und geht **nie** nach aussen (Regel 3);
        dafür gibt es ``datei`` (nur der Name) und :func:`kontext_vermerk`. ``matrix``
        ist ``None`` für die Einheit, sonst 16 Zahlen zeilenweise in der glTF-Welt.
    """
    from pathlib import Path

    from . import kontext as _kontext                       # noqa: PLC0415

    if roh is None:
        return None
    maengel: list[str] = []
    hinweise: list[str] = []
    ergebnis = {"art": None, "ply": None, "datei": None, "matrix": None, "fit": None,
                "crs_note": None, "verortung": None, "massstab": None, "hinweise": hinweise,
                "maengel": maengel}
    if not isinstance(roh, dict):
        maengel.append(f"'context' ist {type(roh).__name__} und kein Block — welche "
                       f"Umgebung gemeint ist, raten wir nicht.")
        return ergebnis

    art = roh.get("kind")
    ergebnis["art"] = art
    if art not in KONTEXT_ARTEN:
        maengel.append(
            f"'context.kind' ist {art!r}. Rendern koennen wir als Umgebung nur "
            f"{list(KONTEXT_ARTEN)}; eine andere Art ohne Umgebung zu rechnen, saehe aus "
            f"wie geliefert.")

    ply = roh.get("ply")
    if not isinstance(ply, str) or not ply.strip():
        maengel.append(f"'context.ply' ist {ply!r} — ohne Datei gibt es keinen Splat.")
    else:
        ergebnis["ply"] = ply
        ergebnis["datei"] = Path(ply).name
        if not Path(ply).is_file():
            maengel.append(
                f"'context.ply': Die Splat-Datei {Path(ply).name!r} liegt auf diesem "
                f"Rechner nicht vor. Gerechnet wird ohne sie NICHT — ein Bild ohne die "
                f"bestellte Umgebung saehe aus wie eines mit.")
        else:
            # EINE GEWOEHNLICHE PUNKTWOLKE IST KEIN SPLAT (Geraeteprobe R59): Sie
            # ging als Splat-Kontext mit, und die Blender-Stufe brach den ganzen Auftrag ab
            # («kein 3DGS-Splat»). Gelesen wird nur der PLY-Kopf. Weggelassen wird sie MIT
            # Satz (`lies_szene` → Warnungen und `qa.verdict.hinweise`), nicht still: Eine
            # Punktwolke ist eine Grundlage und wird direkt gezeigt, nicht ins KI-Bild gemalt.
            from . import kontext_netz as _kontext_netz           # noqa: PLC0415
            fehlend = _kontext_netz.fehlende_splat_felder(ply)
            if fehlend:
                ergebnis["weggelassen"] = _kontext_netz.satz_punktwolke_weggelassen(
                    Path(ply).name, fehlend)
                ergebnis["fehlende_felder"] = list(fehlend)

    transform = roh.get("transform")
    if transform is None:
        hinweise.append("KONTEXT: keine Lage ('transform') mitgesandt — der Splat steht "
                        "so, wie seine Datei es sagt (Einheit in der glTF-Welt).")
    else:
        try:
            ergebnis["matrix"] = list(_kontext.pruefe_matrix(transform))
        except _kontext.KontextError as fehler:
            maengel.append(f"'context.transform': {fehler}")

    fit = roh.get("fit")
    ergebnis["fit"] = fit
    if fit is not None and fit not in KONTEXT_FIT:
        maengel.append(f"'context.fit' ist {fit!r}, bekannt sind {list(KONTEXT_FIT)}. "
                       f"Wie verlaesslich die Lage ist, raten wir nicht.")
    elif fit == "behelf":
        hinweise.append(SATZ_KONTEXT_BEHELF)
    elif fit is None:
        hinweise.append("KONTEXT: Wie die Lage des Splats zustande kam, ist nicht gesagt "
                        "('fit' fehlt) — vermessen ist sie damit nicht belegt.")

    note = roh.get("crs_note")
    if note is not None and not isinstance(note, str):
        maengel.append(f"'context.crs_note' ist {note!r} und kein Satz.")
    elif note:
        ergebnis["crs_note"] = note
        hinweise.append(f"KONTEXT, Bezugssystem: {' '.join(note.split())}")

    verortung = roh.get("verortung")
    if verortung is not None and not isinstance(verortung, str):
        maengel.append(f"'context.verortung' ist {verortung!r} und kein Pfad.")
    elif verortung:
        # NUR DER NAME nach aussen. Gelesen wird seit dem 14.10.2026 nur der Block
        # `massstab` — zur Auskunft; die Lage steht weiter in `transform`.
        ergebnis["verortung"] = Path(verortung).name
        ergebnis["massstab"], saetze = massstab_aus_verortung(verortung)
        hinweise.extend(saetze)
    return ergebnis


#: Die Quellen einer Skizze, die wir rechnen können. Heute nur die Mappe (Entscheid 96).
SKIZZEN_QUELLEN = ("mappe",)

#: Der feste Anfang des Satzes, mit dem ein Nachrender sagt, dass die Skizze beim Modell
#: nicht ankam — derselbe wie :data:`aiimaging.kette.HINWEIS_SKIZZE_NICHT_ANGEKOMMEN`
#: (eine Probe hält beide gleich; hier als Text, damit dieses Modul die Kette nicht lädt).
SKIZZE_NICHT_ANGEKOMMEN_ANFANG = "SKIZZE NICHT ANGEKOMMEN"

#: Der Schlüssel am Geometrieurteil eines Skizzenlaufs (Entscheid 96): ``{name, anweisung,
#: anweisung_aus, unterlage, standpunkt, hinweise}`` — gelesen in :func:`als_ergebnis`.
URTEIL_SKIZZE = "skizze"


#: Auflage A1 des Integrators (15.10.2026): die Höchstlänge eines Skizzennamens — dieselbe
#: wie drüben im Vertrag (``SKIZZENNAME_HOECHSTENS``, ``render-scene.ts``).
SKIZZENNAME_HOECHSTENS = 255


def skizzenname_mangel(name) -> str | None:
    """Ist ``name`` ein RELATIVER Pfad in der Mappe? Der Satz, warum nicht — oder ``None``.

    **Auflage A1 des Integrators (15.10.2026)**, beim Absegnen von ``RenderScene.skizze``: Der
    Name reist von der Knotenansicht zum Heim-PC und wird dort in der Mappe nachgeschlagen. Drüben
    prüft der Vertrag ihn schon (``skizzenNameMangel``); **hier wird unabhängig nochmals
    geprüft** — eine Bildseite, die sich auf die Prüfung des Absenders verlässt, hat keine.

    Abgewiesen wie drüben: kein Text oder leer; länger als :data:`SKIZZENNAME_HOECHSTENS`;
    Steuerzeichen (U+0000–U+001F, U+007F); ein Backslash überhaupt (auch führend); ein führender
    ``/``; ein Laufwerksbuchstabe wie ``C:``; ein Teil ``.`` oder ``..``. Dazu prüfen
    :func:`aiimaging.knotenweg.lege_an` und :func:`aiimaging.abholer.skizzenlauf`, dass der Name
    in der Mappe als Skizze steht.
    """
    if not isinstance(name, str) or not name:
        return f"Der Name der Skizze ist {name!r} — kein Text."
    if len(name) > SKIZZENNAME_HOECHSTENS:
        return (f"Der Name der Skizze ist {len(name)} Zeichen lang — hoechstens "
                f"{SKIZZENNAME_HOECHSTENS}.")
    if any(ord(z) < 0x20 or ord(z) == 0x7F for z in name):
        return "Der Name der Skizze enthaelt ein Steuerzeichen."
    if "\\" in name:
        return ("Der Name der Skizze enthaelt einen Backslash — er ist ein relativer Pfad in "
                "der Mappe, mit «/» getrennt.")
    if name.startswith("/"):
        return "Der Name der Skizze beginnt mit «/» — er ist ein relativer Pfad in der Mappe."
    if len(name) >= 2 and name[1] == ":" and name[0].isascii() and name[0].isalpha():
        return ("Der Name der Skizze beginnt mit einem Laufwerk — er ist ein relativer Pfad in "
                "der Mappe.")
    if any(teil in (".", "..") for teil in name.split("/")):
        return "Der Name der Skizze enthaelt «.» oder «..» als Teil — er bleibt in der Mappe."
    return None


def skizze_aus_szene(roh) -> dict | None:
    """``RenderScene.skizze`` → ``{quelle, name, anweisung, anweisung_original,
    anweisung_sprache, maengel}`` — oder ``None``, wenn keine bestellt ist.

    **Owner-Entscheid 96 (15.10.2026):** Die Skizze vom iPad führt das Bild — in der
    Knotenansicht wie bisher auf der Seite (:func:`aiimaging.arbeitsgang.rechne_skizze`).
    Es reist nur der NAME der Skizze; sie liegt schon in der Mappe am Heim-PC.

    ``anweisung`` ist die Fassung, mit der gerechnet wird — übersetzt wie ``style.prompt``
    (:func:`aiimaging.sprache.uebersetze`), der Wortlaut bleibt in ``anweisung_original``.
    ``None``, wenn keine mitkam: Dann nimmt ``rechne_skizze`` die Bemerkung der Skizze (und
    weist ab, wenn auch die fehlt). ``null`` für das ganze Feld verlangt nichts, wie überall
    (:func:`wert_oder`).
    """
    if roh is None:
        return None
    maengel: list[str] = []
    if not isinstance(roh, dict):
        return {"quelle": None, "name": None, "anweisung": None, "anweisung_original": None,
                "anweisung_sprache": None, "maengel": [
                    f"'skizze' ist {roh!r} und kein Block {{quelle, name, anweisung}}."]}
    quelle = roh.get("quelle")
    if quelle not in SKIZZEN_QUELLEN:
        maengel.append(
            f"'skizze.quelle' ist {quelle!r}. Rechnen koennen wir eine Skizze nur aus der "
            f"Mappe ({', '.join(SKIZZEN_QUELLEN)}) — ein hochgeladenes Bild waere eine "
            f"andere Quelle, die es im Vertrag nicht gibt.")
    name = roh.get("name")
    if not isinstance(name, str) or not name.strip():
        maengel.append(f"'skizze.name' ist {name!r} — welche Skizze gemeint ist, raten wir nicht.")
        name = None
    elif (mangel := skizzenname_mangel(name)) is not None:
        # A1: ein Weg hinaus aus der Mappe wird nicht nachgeschlagen, sondern abgewiesen.
        maengel.append(f"'skizze.name' {name!r}: {mangel}")
        name = None
    roh_anweisung = roh.get("anweisung")
    befund = None
    if roh_anweisung is not None and (not isinstance(roh_anweisung, str)
                                      or not roh_anweisung.strip()):
        maengel.append(
            f"'skizze.anweisung' ist {roh_anweisung!r}. Leer oder kein Text ist keine "
            f"Anweisung — ohne Feld gilt die Bemerkung der Skizze.")
    elif isinstance(roh_anweisung, str):
        befund = sprache.uebersetze(roh_anweisung)
    return {"quelle": quelle if quelle in SKIZZEN_QUELLEN else None, "name": name,
            "anweisung": befund["uebersetzt"] if befund else None,
            "anweisung_original": befund["original"] if befund else None,
            "anweisung_sprache": befund, "maengel": maengel}


def skizze_unvertraeglich(*, kameras, interior, skip, kontext) -> list[str]:
    """Was mit einer Skizze NICHT zusammengeht — je Feld ein Satz (Entscheid 96).

    Dieselben drei Regeln wie drüben im Vertrag (``RenderScene`` superRefine) und eine
    vierte: Eine Umgebung (``context``) käme nicht an — die Skizze rechnet auf ihrer
    Unterlage, nicht in einer Szene. Abgewiesen statt übergangen (E75).
    """
    saetze = []
    if isinstance(kameras, list):
        saetze.append(
            "'cameras' ist eine Liste, aber eine Skizze ist EIN Bild vom Standpunkt der "
            "Mappe (wie «aus Skizze rechnen» auf der Seite) — cameras weglassen oder 'auto'.")
    elif kameras == "saved":
        saetze.append("'cameras: saved' und eine Skizze gehen nicht zusammen — die Skizze ist "
                      "EIN Bild vom Standpunkt der Mappe.")
    if interior is not None:
        saetze.append("'interior' und eine Skizze gehen nicht zusammen — die Skizze ist EIN Bild.")
    if skip is True:
        saetze.append("'vis.skip: true' und eine Skizze: Ohne Bildmodell gibt es nichts, das "
                      "die Skizze liest.")
    if kontext is not None:
        saetze.append("'context' und eine Skizze: Die Skizze rechnet auf ihrer Unterlage, eine "
                      "Umgebung (Splat) kaeme nicht an.")
    return saetze


def skizze_saetze(vermerk) -> list[str]:
    """Die Auskunft eines Skizzenlaufs für ``verdict.hinweise`` — leer ohne Vermerk."""
    if not isinstance(vermerk, dict):
        return []
    name = vermerk.get("name") or "?"
    if vermerk.get("anweisung_aus") == "bemerkung":
        woher = "Anweisung aus der Bemerkung der Skizze"
    elif vermerk.get("anweisung_aus") == "prompt":
        # Befund F4 (24.10.2026): die Skizze hatte keine Bemerkung (nur einen gewünschten Namen),
        # darum galt der Prompt der Bestellung (Rückfall 96c, auch am Heim-PC).
        woher = (f"Anweisung aus dem Prompt am Render-Knoten "
                 f"({vermerk.get('anweisung')!r}, die Skizze hat keine Bemerkung)")
    else:
        woher = f"Anweisung: {vermerk.get('anweisung_original') or vermerk.get('anweisung')!r}"
    saetze = [f"AUS SKIZZE GERECHNET: {name!r} auf ihrer Unterlage, {woher} — wie «aus Skizze "
              f"rechnen» auf der Seite."]
    unterlage = (vermerk.get("unterlage") or {}).get("grund")
    if unterlage:
        saetze.append(str(unterlage))
    standpunkt = vermerk.get("standpunkt")
    if standpunkt:
        saetze.append(str(standpunkt))
    return saetze


def kontext_vermerk(kontext: dict | None, bericht: dict | None = None) -> dict | None:
    """Was vom Kontext nach aussen geht — **ohne Pfad** (Regel 3).

    Aus der gelesenen Bestellung (:func:`kontext_aus_szene`) und, wenn da, dem Block
    ``kontext`` des Blender-Berichts: Datei (Name, sha256), Lage (``fit``, ``crs_note``),
    Punktzahlen und der Anteil des Modells, den der Splat verdeckt.

    **Seit dem 13.10.2026 (Entscheid 79) mit dem Weg:** ``weg`` ist ``"realityscan"`` (Netz
    aus den Fotos, Entscheid 81; ``realityscan_grund`` sagt sonst, warum nicht), ``"netz"`` (die
    Splat-Brücke hat ein Netz geliefert) oder ``"kugeln"`` (Notlösung), ``netz`` die
    Kennzahlen des Netzes (Ecken, Dreiecke, sha256, Blickwinkel, Voxel — kein Pfad),
    ``netz_grund`` warum es Kugeln wurden. Gesetzt vom Abholer
    (``seams.kontext_vorbereiten``); fehlt die Angabe, sagt es der Blender-Bericht
    (``quelle``).
    """
    from . import kontext_netz as _kontext_netz            # noqa: PLC0415 — stdlib

    if not kontext:
        return None
    block = (bericht or {}).get("kontext") or {}
    verdeckung = block.get("verdeckung") or {}
    weg = kontext.get("weg")
    if weg is None and block.get("quelle"):
        weg = "netz" if block.get("quelle") == _kontext_netz.QUELLE_NETZ else "kugeln"
    return {
        "art": kontext.get("art"),
        "datei": kontext.get("datei"),
        "weg": weg,
        "netz": kontext.get("netz"),
        "netz_grund": kontext.get("netz_grund"),
        # Seit Entscheid 81 (13.10.2026): warum RealityScan nicht benutzt wurde — ohne Pfad.
        "realityscan_grund": kontext.get("realityscan_grund"),
        "sha256": block.get("sha256"),
        "fit": kontext.get("fit"),
        "crs_note": kontext.get("crs_note"),
        # Seit dem 14.10.2026: wie verlaesslich der Massstab ist (Ampel von KosmoPrepare).
        "massstab": kontext.get("massstab"),
        "matrix_angewandt": kontext.get("matrix") is not None,
        "punkte_gerendert": block.get("punkte_gerendert"),
        "verworfen_deckkraft": block.get("verworfen_deckkraft"),
        "verdeckt_anteil": verdeckung.get("anteil"),
        "hinweise": list(kontext.get("hinweise") or ()),
    }


def kontext_saetze(vermerk) -> list[str]:
    """Die Saetze fuer ``verdict.hinweise`` zu einem :data:`URTEIL_KONTEXT`-Vermerk.

    **In ``hinweise`` und nicht in ``reason``**, aus demselben Grund wie
    :func:`aufsicht_satz`: Eine Umgebung ist bestellt, nicht missraten. Der erste Satz sagt,
    dass gemessen nur das Bauwerk wird; die folgenden kommen aus der Bestellung (``fit``,
    ``crs_note``).
    """
    if not isinstance(vermerk, dict) or not vermerk.get("datei"):
        return []
    # Der verdeckte Anteil steht NICHT im Satz: Er gilt je Kamera, der Satz je Auftrag.
    # Er steht im Vermerk am Kameraurteil (befund.json, urteil.json).
    return [f"UMGEBUNG: Splat {vermerk['datei']!r} im Bild — sichtbar in Bild und Tiefe, "
            f"gemessen wird nur das Bauwerk.",
            *[s for s in vermerk.get("hinweise") or () if s]]


#: Der Wert von glTF ``extras.role``, mit dem KosmoOrbit einen **Bestandskörper** markiert
#: (Integrator, Runde 14, 08.10.2026) — ein Körper aus dem Splat, kein Entwurf.
BESTAND_ROLLE = "existing"

#: Was dem Bildauftrag angehängt wird, wenn die glb Bestand trägt (Splat-Demolauf
#: 08.10.2026: das Modell erfand an der Halle Fassade und Fantasie-Schriftzug).
#:
#: **Positiv formuliert, nicht als negativer Prompt.** Der negative Prompt wirkt auf dem
#: Vorgabe-Backbone nicht (``z-image-turbo``, Führung 0 — siehe
#: ``abholer.RENDER_STEHENGEBLIEBEN``); er stünde im Protokoll und änderte keinen
#: Bildpunkt. Ob der Zusatz die Schrift wirklich verhindert, ist **ungemessen**
#: (Messauftrag ``auf-20261008-271``).
BESTAND_ZUSATZ = ("existing building shown as a plain massing volume, "
                  "blank facade without lettering or signage")

#: Der Schluessel, unter dem ein Kameraurteil den Bestand des Laufs vermerkt.
URTEIL_BESTAND = "bestand"


def bestand_in_glb(pfad) -> dict | None:
    """Wie viele Knoten der glb als Bestand markiert sind (``extras.role == "existing"``).

    Gelesen wird nur der JSON-Block der Datei — ohne trimesh, ohne Blender. ``None``, wenn
    kein Knoten Bestand ist, die Datei keine glb/gltf ist oder sich nicht lesen lässt:
    Dann bleibt der Bildauftrag, wie er kam. Ein unlesbarer Kopf ist hier kein Mangel —
    den meldet der Multipass, der dieselbe Datei gleich danach öffnet.
    """
    import json as _json
    import struct as _struct
    from pathlib import Path as _Path
    try:
        pfad = _Path(pfad)
        daten = pfad.read_bytes()
        if pfad.suffix.lower() == ".gltf":
            js = _json.loads(daten)
        else:
            laenge, art = _struct.unpack_from("<II", daten, 12)
            if art != 0x4E4F534A:
                return None
            js = _json.loads(daten[20:20 + laenge])
    except (OSError, ValueError, _struct.error, TypeError):
        return None
    knoten = [k for k in js.get("nodes") or () if isinstance(k, dict)]
    mit_mesh = [k for k in knoten if "mesh" in k]
    bestand = [k for k in knoten
               if isinstance(k.get("extras"), dict)
               and k["extras"].get("role") == BESTAND_ROLLE]
    if not bestand:
        return None
    return {"n_bestand": len(bestand), "n_knoten": len(mit_mesh),
            "namen": [str(k.get("name") or "") for k in bestand][:20]}


#: Die Werte von glTF ``extras.role``, mit denen eine Datei einen Knoten als **Boden bzw.
#: Gelände** ausweist (auf-20261021-316, B3; Vorgabe an KosmoDraw 21.10.2026). Dasselbe Feld
#: wie :data:`BESTAND_ROLLE` — KosmoOrbit schreibt ``extras.role`` schon heute
#: (``derive/gltf.ts``, ``bestandExtras``), eine zweite Stelle für dieselbe Art Angabe wäre
#: eine zweite Konvention. ``"terrain"`` wird mitgelesen, vorgegeben wird ``"ground"``.
#: Seit Ergebnis 341 (23.10.2026) steht die Aufzählung in :data:`aiimaging.maske.GELAENDE_ROLLEN`
#: — auch der Blender-Runner liest sie, und eine Regel gehört an eine Stelle.
from .maske import GELAENDE_ROLLEN  # noqa: E402


def _glb_kopf(pfad) -> dict | None:
    """Der JSON-Block einer glb/gltf — ohne trimesh, ohne Blender; ``None``, wenn unlesbar."""
    import json as _json
    import struct as _struct
    from pathlib import Path as _Path
    try:
        pfad = _Path(pfad)
        daten = pfad.read_bytes()
        if pfad.suffix.lower() == ".gltf":
            js = _json.loads(daten)
        else:
            laenge, art = _struct.unpack_from("<II", daten, 12)
            if art != 0x4E4F534A:
                return None
            js = _json.loads(daten[20:20 + laenge])
    except (OSError, ValueError, _struct.error, TypeError):
        return None
    return js if isinstance(js, dict) else None


def gelaende_in_glb(pfad) -> dict | None:
    """Welche Knoten die glb selbst als Boden ausweist (``extras.role`` in :data:`GELAENDE_ROLLEN`).

    **Warum die Rolle und nicht der Name** (auf-20261021-316, B3). Die Probedatei von
    KosmoDraw nennt ihren Boden «boden» — Knoten, Mesh und Material. Die Geländeregel der
    Maske nimmt dieses Wort mit Grund nie auf (:data:`aiimaging.maske.WOERTER_AUSDRUECKLICH_NICHT`:
    ein Geschossboden ist kein Gelände), und so zählte der Boden als Bauwerk. Was die Namen
    nicht tragen können, sagt die Datei: ``extras.role = "ground"`` am Knoten.

    Returns:
        ``None`` ohne solchen Knoten oder bei unlesbarer Datei. Sonst
        ``{"n_gelaende", "knoten", "materialien", "geteilt", "namen"}``:

        * ``knoten`` — die Knotennamen (sie stehen in der Tabelle, wenn der Runner
          Objektnamen vergibt);
        * ``materialien`` — Materialnamen, die **nur** an solchen Knoten hängen (sie stehen
          in der Tabelle, wenn der Runner Materialnamen vergibt);
        * ``geteilt`` — Materialnamen, die ein Boden mit einem anderen Knoten teilt. Sie
          werden **nicht** übertragen: Im Material-ID-Pass trügen beide dieselbe Kennfarbe,
          und den Boden hinauszunehmen hiesse, das Bauwerk mit hinauszunehmen;
        * ``namen`` — ``knoten`` und ``materialien`` zusammen, so wie
          :func:`aiimaging.maske.bauwerksmaske` sie als ``gelaende_rolle`` nimmt.
    """
    js = _glb_kopf(pfad)
    if js is None:
        return None
    knoten = [k for k in js.get("nodes") or () if isinstance(k, dict)]
    meshes = [m for m in js.get("meshes") or () if isinstance(m, dict)]
    materialien = [m for m in js.get("materials") or () if isinstance(m, dict)]

    def ist_boden(k) -> bool:
        extras = k.get("extras")
        return (isinstance(extras, dict)
                and str(extras.get("role") or "").strip().lower() in GELAENDE_ROLLEN)

    def materialnamen(k) -> set[str]:
        i = k.get("mesh")
        if not isinstance(i, int) or not 0 <= i < len(meshes):
            return set()
        namen = set()
        for prim in meshes[i].get("primitives") or ():
            j = prim.get("material") if isinstance(prim, dict) else None
            if isinstance(j, int) and 0 <= j < len(materialien):
                namen.add(str(materialien[j].get("name") or ""))
        return namen - {""}

    boden = [k for k in knoten if ist_boden(k)]
    if not boden:
        return None
    am_boden = set().union(*(materialnamen(k) for k in boden))
    sonst = set().union(set(), *(materialnamen(k) for k in knoten
                                 if "mesh" in k and not ist_boden(k)))
    knotennamen = [str(k.get("name") or "") for k in boden if k.get("name")]
    eigen = sorted(am_boden - sonst)
    return {"n_gelaende": len(boden), "knoten": knotennamen[:50], "materialien": eigen,
            "geteilt": sorted(am_boden & sonst),
            "namen": list(dict.fromkeys([*knotennamen[:50], *eigen]))}


def glb_mit_rolle(quelle, ziel, knoten: str, rolle: str = GELAENDE_ROLLEN[0]) -> dict:
    """Eine Kopie der glb, in der ein Knoten ``extras.role = rolle`` trägt — sonst bytegleich.

    Für die Messung am Heim-PC (Auftrag zur Steine-Probe, auf-20261021-316 B3): Die Probedatei
    trägt die Rolle noch nicht; mit dieser Kopie lässt sich der Weg prüfen, bevor die nächste
    Ausfuhr sie mitbringt. Geändert wird nur der JSON-Block (neu auf vier Bytes aufgefüllt),
    der Binärblock wandert unverändert mit. Die Quelle bleibt unberührt.

    Returns:
        ``{"ziel", "knoten", "rolle", "bytes"}``.

    Raises:
        ValueError: keine glb, kein oder mehr als ein Knoten dieses Namens.
    """
    import json as _json
    import struct as _struct
    from pathlib import Path as _Path
    daten = _Path(quelle).read_bytes()
    if len(daten) < 20 or daten[:4] != b"glTF":
        raise ValueError("Keine glb (Kopf 'glTF' fehlt).")
    laenge, art = _struct.unpack_from("<II", daten, 12)
    if art != 0x4E4F534A:
        raise ValueError("Der erste Block der glb ist kein JSON.")
    js = _json.loads(daten[20:20 + laenge])
    rest = daten[20 + laenge:]
    treffer = [k for k in js.get("nodes") or () if isinstance(k, dict) and k.get("name") == knoten]
    if len(treffer) != 1:
        raise ValueError(f"{len(treffer)} Knoten heissen {knoten!r} — erwartet genau einer.")
    extras = treffer[0].get("extras") if isinstance(treffer[0].get("extras"), dict) else {}
    treffer[0]["extras"] = {**extras, "role": str(rolle)}
    roh = _json.dumps(js, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    roh += b" " * (-len(roh) % 4)
    gesamt = 12 + 8 + len(roh) + len(rest)
    aus = (daten[:4] + _struct.pack("<II", _struct.unpack_from("<I", daten, 4)[0], gesamt)
           + _struct.pack("<II", len(roh), 0x4E4F534A) + roh + rest)
    _Path(ziel).write_bytes(aus)
    return {"ziel": str(ziel), "knoten": knoten, "rolle": str(rolle), "bytes": len(aus)}


def bildauftrag_bestand(prompt: str, bestand: dict | None) -> dict | None:
    """Den Bildauftrag um :data:`BESTAND_ZUSATZ` ergänzen — nur, wenn Bestand da ist.

    Returns:
        ``None`` ohne Bestand, sonst ``{bestellt, gerechnet, zusatz, n_bestand, n_knoten}``.
    """
    if not bestand or not isinstance(prompt, str):
        return None
    gerechnet = f"{prompt.rstrip(' ,')}, {BESTAND_ZUSATZ}" if prompt.strip() else BESTAND_ZUSATZ
    return {"bestellt": prompt, "gerechnet": gerechnet, "zusatz": BESTAND_ZUSATZ,
            "n_bestand": bestand.get("n_bestand"), "n_knoten": bestand.get("n_knoten")}


#: Der Satz, wenn eine Umgebung bestellt ist, aber kein Körper als Bestand markiert ist
#: (Vorschlag des Integrators zu ``auf-20261014-283``: Dort fehlte dem Volumen ``program
#: «bestand»``, darum fehlte ``role existing`` und mit ihm der Bestandszusatz — die Prüfung
#: fiel 0.000/0.786/0.787, dieselbe glb mit der Rolle bestand 0.965/0.953/0.953).
BESTAND_FEHLT_SATZ = ("BESTAND FEHLT: Eine Umgebung ist bestellt, aber kein Körper ist als Bestand "
                      "markiert — der Bildauftrag läuft ohne Bestandszusatz, und die Prüfung kann "
                      "daran fallen. In KosmoOrbit das Volumen als Bestand anlegen (Programm "
                      "«Bestand») oder «als Bestand übernehmen».")


def bestand_vermerk(bestand_auftrag: dict | None, kontext) -> dict | None:
    """Der :data:`URTEIL_BESTAND`-Vermerk einer Kamera: der Zusatz, wenn Bestand da ist;
    ``{"fehlt": True}``, wenn eine Umgebung bestellt ist, aber kein Bestand markiert;
    sonst ``None``. Eine Warnung, kein Abbruch — gerechnet wird trotzdem."""
    if bestand_auftrag:
        return bestand_auftrag
    if kontext is not None:
        return {"fehlt": True}
    return None


def bestand_satz(vermerk) -> str | None:
    """Der Satz für ``verdict.hinweise`` zu einem :data:`URTEIL_BESTAND`-Vermerk."""
    if isinstance(vermerk, dict) and vermerk.get("fehlt"):
        return BESTAND_FEHLT_SATZ
    if not isinstance(vermerk, dict) or not vermerk.get("n_bestand"):
        return None
    return (f"BESTAND: {vermerk['n_bestand']} Körper als bestehend markiert; dem Bildauftrag "
            f"wurde «{vermerk['zusatz']}» angehängt (ohne Schrift). Ob das Bild ohne "
            f"Schrift bleibt, ist ungemessen.")


def wert_oder(quelle: dict, schluessel: str, ersatz):
    """Ein Feld der fremden Bestellung lesen — und ein ausdrückliches ``null`` wie ein
    fehlendes Feld behandeln.

    **Warum das nicht ``dict.get(schluessel, ersatz)`` sein darf.** Der zweite Parameter
    greift **nur bei fehlendem Schlüssel**. Steht das Feld da und trägt ``null``, gewinnt
    die ``None`` gegen den Ersatz — und gleich darauf wirft ``int(None)`` oder
    ``float(None)``.

    Das ist keine erdachte Lage: Wer die Vorgabe des Vertrags gelten lassen will, schreibt
    in JSON genau ``"samples": null``. Am 22.09.2026 nachgestellt: **Ein einziger solcher
    Auftrag reisst den ganzen Abholdurchgang mit** — der ``TypeError`` fällt durch
    ``except quelle.QUELLEN_FEHLER`` hindurch (das ist nur ``BrueckenError``) bis in
    ``abholer.durchgang``, und weil der kaputte Auftrag auf ``queued`` stehenbleibt,
    stolpert **jeder** folgende Lauf wieder über ihn. Eine dauerhaft verstopfte
    Warteschlange, und die eigene Ablage steht mit still, weil die Brücke in derselben
    Schleife zuerst drankommt.

        *Ein Auftrag, den wir nicht lesen können, ist ein Mangel an diesem Auftrag — und
        nicht das Ende des Durchgangs.*

    Derselbe Griff hat am 21./22.09.2026 schon an zwei anderen Stellen zugeschlagen
    (`homeworker._darf_starten`, `kette._fuehre_geometrie`). Dreimal an drei Tagen ist
    kein Ausrutscher; darum steht hier eine Funktion und keine dritte Einzelreparatur.

    Args:
        quelle: Der Block aus der fremden Bestellung.
        schluessel: Das Feld.
        ersatz: Was gilt, wenn das Feld fehlt **oder** ``null`` trägt.
    """
    wert = quelle.get(schluessel)
    return ersatz if wert is None else wert


#: Die groesste Samplezahl, die angenommen wird: 2 hoch 24 = 16'777'216.
#:
#: **Warum eine Obergrenze** (Durchsicht der Runde 7b, 23.09.2026): Der MCP-Einlass nahm
#: ``samples: 1e300`` und ``2**63`` an und legte den Auftrag auf ``queued``. Wirken kann
#: das nicht — der Runner reicht die Zahl an Blender weiter
#: (``runners/blender_depth_stage.py``, ``szene.cycles.samples = a.samples``), und dort
#: ist sie begrenzt.
#:
#: **Woher die Zahl stammt — gesetzt aus dem Quelltext, SEIT DEM 23.09.2026 AUCH GEMESSEN**
#: an Blender 5.2.2 LTS auf der HomeStation (``auf-20260923-151`` V7: ``hard_max`` von
#: ``samples`` 16777216, von ``resolution_x`` 65536 — dieselben). Im Bestand dieses Repos nimmt
#: keine Stelle eine Obergrenze an: weder Runner (``--samples``, ``type=int``) noch Kette
#: (``int(samples)``) noch der fremde Vertrag, soweit er hier abgebildet ist. Die Zahl
#: ist die harte Grenze, die die Cycles-Erweiterung von Blender ihrer Eigenschaft
#: ``samples`` gibt (``max=(1 << 24)``) — nachgelesen am 23.09.2026 im Quelltext von
#: Blender 4.2.0 (``intern/cycles/blender/addon/properties.py``). Ob Blender darueber
#: klemmt oder abweist, ist
#: ebenfalls nicht gemessen; wie bestellt waere es in keinem der beiden Faelle. Die
#: groesste Zahl, die hier je bestellt wurde, sind 220'000 Samples (HomeStation,
#: ``auftraege/ergebnisse/auf-20260820-18.json``) — weit darunter.
#:
#: Die Grenze sagt nur: DARUEBER kann die Angabe nicht wirken. Dass darunter jeder Lauf
#: in seiner Frist fertig wird, sagt sie nicht.
SAMPLES_HOECHSTENS = 1 << 24

#: Die groesste Kantenlaenge in Pixeln, die angenommen wird: 65'536.
#:
#: Derselbe Befund und dieselbe Herkunft wie bei :data:`SAMPLES_HOECHSTENS`, GESETZT,
#: NICHT GEMESSEN: Blenders ``RenderSettings.resolution_x`` ist laut Quelltext von
#: Blender 4.2.0 (``makesrna/intern/rna_scene.cc``, nachgelesen am 23.09.2026) auf 4 bis
#: 65'536 begrenzt; der Runner setzt beide aus
#: ``--aufloesung``/``--hoehe``. Nach unten gilt ohnehin das Raster von 16
#: (:func:`_auf_raster`), und 65'536 ist ein Vielfaches davon.
KANTE_HOECHSTENS = 1 << 16

#: DIE EINE REGEL fuer eine Kantenlaenge — gelesen in :func:`lies_szene`
#: (``render.resolution``), am MCP-Einlass (``aufloesung``) und in beiden Richtungen der
#: Auftragsnaht (:func:`aiimaging.kosmo_naht.aufloesung_zu_resolution`, seit der Runde 8
#: auch :func:`aiimaging.kosmo_naht.resolution_zu_aufloesung`). Als Woerterbuch hier,
#: damit keiner von ihnen eine eigene Fassung fuehrt (Runde 7c, 23.09.2026).
REGEL_KANTE = {"ganzzahlig": True, "mindestens": 1, "hoechstens": KANTE_HOECHSTENS}

#: DIE EINE REGEL fuer die Samplezahl — in :func:`lies_szene` und am MCP-Einlass.
REGEL_SAMPLES = {"ganzzahlig": True, "mindestens": 1, "hoechstens": SAMPLES_HOECHSTENS}

#: DIE REGEL fuer ``render.faithful`` — ein Regler von 0 bis 1, so steht er im fremden
#: Vertrag (``docs/OEKOSYSTEM_2026-08-18.md``: «0..1, 1.0 = Cycles-treu ↔ 0.0 = KI-frei»)
#: und so liest ihn :func:`lies_szene` als ``controlnet_staerke``.
#:
#: **Der Befund** (Runde 8, 23.09.2026): ``faithful: 5.0`` ging ohne Mangel durch und
#: stand als ``controlnet_staerke 5.0`` in der Szene. Abgewiesen haette ihn erst
#: ``render.pruefe_auftrag`` (``controlnet_staerke`` ausserhalb von 0..1) — laut
#: Quelltext NACH der Blender-Stufe, beim Rendern; nachgefahren ist dieser spaete Weg
#: nicht. Seither ein Mangel beim Lesen, bevor etwas gerechnet wird.
#:
#: **Seit der Runde 9 auch am MCP-Einlass** (23.09.2026). Bis dahin stand hier «nur hier
#: und nicht am MCP-Einlass», und das stimmte in der schlechten Richtung:
#: :func:`aiimaging.werkzeuge.enqueue_render` UEBERGING ein ``faithful`` im Aufruf still —
#: der Auftrag wurde mit der Vorgabe 0.8 gerechnet. Seither liest der Einlass es mit
#: dieser Regel, legt die gelesene Zahl ab, :func:`aiimaging.kosmo_naht.als_render_scene`
#: schreibt sie als ``render.faithful`` in die Szene, und :func:`lies_szene` liest sie
#: wieder mit dieser Regel — bis zur ``controlnet_staerke`` des Abholers.
REGEL_TREUE = {"ganzzahlig": False, "mindestens": 0, "hoechstens": 1}


def lies_zahl(wert, feld: str, *, ganzzahlig: bool, mindestens=None, hoechstens=None):
    """Eine Zahl der Bestellung lesen — ``(zahl, None)`` oder ``(None, satz)``.

    **Der Befund** (Durchsicht der Runde 7, nachgestellt am 23.09.2026): Eine
    ``render-scene.json`` mit ``render.samples: "viele"`` warf in :func:`lies_szene` einen
    nackten ``ValueError`` aus ``int(...)``; ``resolution: ["x", 1024]`` ebenso,
    ``faithful: "hoch"`` aus ``float(...)``, und ``Infinity`` — das Python-JSON liest es —
    einen ``OverflowError``. :func:`aiimaging.bruecke.lies_auftrag` fing nur
    ``SzenenError``; der Fehler riss ``abholer.durchgang`` und mit ihm
    ``tools/abholen.py`` heraus, und kein weiterer Auftrag der Ablage wurde angesehen.

    Und was NICHT warf, war schlimmer: ``samples: true`` ergab still 1 Sample, ``1.5``
    still 1, ``-3`` ging so an den Runner. Angenommen und nicht wie bestellt.

    **Ein Satz statt einer Ausnahme**, weil es dem Muster von :func:`lies_szene` folgt:
    ``SzenenError`` steht dort nur, wo es gar nichts zu rendern gibt (kein Block, kein
    ``geometry.path``); ein Feld, das sich nicht deuten laesst, ist ein Mangel mit Satz
    (``geometry.format``, ``gelaende``, ``interior``). So sieht der Besteller ALLE
    unlesbaren Felder auf einmal und nicht nur das erste.

    **Auch eine zu grosse ganze Zahl ist ein Satz** (Durchsicht der Runde 7b,
    23.09.2026). Das JSON kennt keine Obergrenze, und Python liest ``1`` mit 400 Nullen
    als ``int``; ``math.isfinite`` und ``float(...)`` warfen darauf ``OverflowError`` —
    genau die Ausnahme, die diese Funktion ersetzen sollte. Ganze Zahlen werden darum
    nie in ``float`` umgewandelt, bevor sie verglichen sind, und im Satz erscheint eine
    riesige Zahl als Stellenzahl statt als 400 Ziffern.

    **Wer sie ruft** (vollstaendig nachgezaehlt am 23.09.2026, Runde 9 — die Liste hier
    war zuvor unvollstaendig):

    * :func:`lies_szene` — ``render.resolution`` (:data:`REGEL_KANTE`),
      ``render.samples`` (:data:`REGEL_SAMPLES`), ``render.faithful``
      (:data:`REGEL_TREUE`);
    * der MCP-Einlass :func:`aiimaging.werkzeuge.enqueue_render` — ``aufloesung``,
      ``samples`` und seit der Runde 9 ``faithful``, mit denselben drei Regeln;
    * beide Richtungen der Auftragsnaht, :func:`aiimaging.kosmo_naht.aufloesung_zu_resolution`
      und :func:`aiimaging.kosmo_naht.resolution_zu_aufloesung`, mit :data:`REGEL_KANTE`;
    * :func:`_lies_kamerapunkt` (seit der Runde 9) fuer jede Koordinate der drei
      Kamerafunktionen, ``ganzzahlig=False`` ohne Bereich.

    Was an einer dieser Stellen angenommen wird, liest :func:`lies_szene` auch — eine
    Regel, nicht zwei.

    Args:
        wert: der Wert, wie er ankam (``null`` hat der Aufrufer schon ersetzt).
        feld: der Punktpfad fuer den Satz.
        ganzzahlig: ``True``: nur ganze Zahlen; ``64.0`` gilt als 64, ``1.5`` nicht —
            abgeschnitten waere es ein anderes Bild als das bestellte.
        mindestens: kleinster zulaessiger Wert, oder ``None``.
        hoechstens: groesster zulaessiger Wert, oder ``None`` (seit der Runde 7c).

    Returns:
        ``(zahl, None)`` — ``int`` bei ``ganzzahlig``, sonst ``float`` — oder
        ``(None, satz)``. ``None`` heisst NICHT GELESEN, nicht 0.
    """
    erwartet = ("eine ganze Zahl" if ganzzahlig else "eine endliche Zahl") + (
        f" ab {mindestens}" if mindestens is not None else "") + (
        f" bis {hoechstens}" if hoechstens is not None else "")
    grund = None
    zahl = None
    if isinstance(wert, bool):
        grund = "ein Wahrheitswert ist keine Zahl (true waere still 1)"
    elif not isinstance(wert, (int, float)):
        grund = f"{type(wert).__name__} ist keine Zahl"
    elif isinstance(wert, float) and not math.isfinite(wert):
        grund = "keine endliche Zahl"
    elif ganzzahlig:
        # Eine ganze Zahl bleibt `int`, egal wie gross; ein `float` ist es nur, wenn er
        # keinen Rest hat — und dann ist `int(...)` exakt.
        if isinstance(wert, float) and not wert.is_integer():
            grund = ("keine ganze Zahl — abgeschnitten waere es ein anderes Bild als "
                     "bestellt")
        else:
            zahl = int(wert)
    else:
        try:
            zahl = float(wert)
        except OverflowError:  # eine ganze Zahl jenseits des Gleitkommabereichs
            grund = "ausserhalb dessen, was eine Gleitkommazahl fassen kann"
    if grund is None and mindestens is not None and zahl < mindestens:
        grund = "zu klein"
    if grund is None and hoechstens is not None and zahl > hoechstens:
        grund = "zu gross — darueber kann die Angabe nicht wirken"
    if grund is not None:
        return None, (
            f"'{feld}' ist {_zeige(wert)}, erwartet war {erwartet}: {grund}. Das Feld "
            f"wird weder geraten noch durch die Vorgabe ersetzt — abgewiesen statt still "
            f"anders gerechnet.")
    return zahl, None


def _zeige(wert) -> str:
    """Ein Wert fuer den Satz — eine riesige ganze Zahl als Stellenzahl.

    ``repr`` einer ganzen Zahl mit ueber 4300 Stellen wirft in Python ab 3.11 selbst
    ``ValueError`` (Grenze der Umwandlung in Text), und 400 Ziffern im Satz liest
    niemand. Die Stellenzahl ist aus der Bitlaenge geschaetzt, darum «rund».
    """
    if isinstance(wert, int) and not isinstance(wert, bool) and wert.bit_length() > 64:
        stellen = int(wert.bit_length() * math.log10(2)) + 1
        # DAS VORZEICHEN GEHT MIT (23.09.2026): «rund 401 Stellen … zu klein» las sich
        # widerspruechlich, solange nicht dastand, dass die Zahl negativ ist.
        art = "negative ganze Zahl" if wert < 0 else "ganze Zahl"
        return f"eine {art} mit rund {stellen} Stellen"
    try:
        return repr(wert)
    except ValueError:
        # EINE RIESIGE ZAHL IN EINEM BLOCK (Runde 9, 23.09.2026): `[10**5000]` als
        # Koordinate oder als `render.samples` — `repr` der Liste ruft `repr` der Zahl
        # und wirft dieselbe Grenze. Der Satz nennt dann die Art, nicht den Inhalt.
        return (f"ein {type(wert).__name__} mit einer ganzen Zahl von über 4300 "
                f"Stellen darin")


def _zeige_punkt(punkt) -> str:
    """Ein Kamerapunkt fuer den Satz — jede Koordinate durch :func:`_zeige`.

    ``repr`` einer Liste ruft ``repr`` jeder Zahl darin, und eine ganze Zahl mit ueber
    4300 Stellen wirft dabei selbst ``ValueError`` (Runde 8, 23.09.2026): Der Satz, der
    den Fehler erklaeren sollte, wurde zum Fehler.
    """
    if isinstance(punkt, (list, tuple)):
        return "[" + ", ".join(_zeige(v) for v in punkt) + "]"
    return _zeige(punkt)


def _lies_interior(roh, *, kameras, fmt: str, warnungen: list, maengel: list):
    """``interior`` → ``(innenraum, bestellt)``: was wir rechnen, und was bestellt war.

    **Der Befund** (22.09.2026, Antworten auf auf-104, auf-31 und auf-91, übertragen am
    selben Tag): KosmoOrbit sendet seit dem 19.09.2026 ``interior: {rooms: "auto"}``
    zusammen mit ``geometry.format: "ifc"``, und unsere Karte kannte das Feld nicht. Jede
    Innenraum-Bestellung lief damit in den Riegel für unbekannte Felder.

    Was belegt ist, und nur das wird angenommen:

    * ``rooms: "auto"`` — die einzige gesendete Form, je Auftrag **ein** Innenstandpunkt.
      Bei uns heisst das: der erste Raum mit brauchbarem Standpunkt
      (``raumkamera.waehle(raum=None)``), frontal — ein ``view``-Feld ist drüben bewusst
      nicht gebaut, und frontal ist unsere Vorgabe (``kette._fuehre_multipass``).
    * **Mitgesandte Kameras gehen vor, und zwar als Auflösung, nicht als Rangfolge.**
      Drüben leitet der eigene Kern die Standpunkte ab und schickt sie als benannte
      Kameras mit; eine Portierung unserer Rechenregel wird nicht verlangt (auf-91 V1/V2).
      Das ``"auto"`` ist in diesem Fall also schon beantwortet. Einen zweiten
      Innenstandpunkt dazuzurechnen widerspräche auf-31 R6 («keine zwei
      Innenstandpunkte je Raum») — gerendert werden die Kameras, und eine Warnung sagt es.

    Was **nicht** belegt ist, wird mit einem Satz abgewiesen: eine Raumliste (Name?
    IFC-Kennung? Objekt?), ein fehlendes ``rooms`` und ein ``interior``, das kein Block
    ist.

    **Und ein ``interior`` ohne IFC — aber nur, wenn keine Kameras mitkommen**
    (Durchsicht 22.09.2026: Hier stand bis dahin ohne Einschränkung «ein interior ohne IFC
    wird abgewiesen», und die Reihenfolge darunter tat das nicht). Die Kameraliste wird
    zuerst geprüft und kehrt zurück, denn mit ihr braucht es keine Räume: Der Standpunkt
    ist gegeben, gerechnet wird keiner. Ohne Kameraliste müsste er aus den Räumen kommen,
    und Räume gibt es nur in der IFC — aus einer glb lässt sich kein Raumbegriff gewinnen.
    Beide Fälle bewacht in ``tests/test_interior_bestellung.py``.

    **Was bestellt war, reist in beiden Fällen weiter** (Durchsicht 23.09.2026). Bis
    dahin kehrte der Zweig mit Kameraliste mit ``None`` zurück, und die Tatsache «die
    Bestellung sagte ``interior``» ging an genau der Form verloren, in der KosmoOrbit
    **jede** Innenbestellung sendet (auf-91 V1: immer mit benannten Kameras). Ein
    Innenbild kam dann drüben ohne jeden Vermerk an und sah aus wie ein missratenes
    Aussenbild. Darum zwei Rückgabewerte: ``innenraum`` sagt, ob WIR einen Standpunkt
    rechnen; ``bestellt`` sagt, ob ``interior`` bestellt und angenommen war.

    Returns:
        ``(innenraum, bestellt)``. ``innenraum`` ist
        ``{"raum": None, "art": "frontal", "bestellt": {"rooms": "auto"}}`` — nur ohne
        Kameraliste und mit IFC — oder ``None``. ``bestellt`` ist ``{"rooms": "auto"}``,
        wenn ``interior`` angenommen wurde (mit oder ohne Kameraliste), sonst ``None``
        (nicht bestellt oder abgewiesen).
    """
    if roh is None:
        return None, None
    if not isinstance(roh, dict):
        maengel.append(
            f"'interior' ist {type(roh).__name__} und kein Block. Belegt ist bei euch "
            f"nur {{rooms: '{INTERIOR_ROOMS_AUTO}'}} (auf-31 R3); was ein anderer Wert "
            f"verlangt, raten wir nicht.")
        return None, None
    raeume = roh.get("rooms")
    if raeume != INTERIOR_ROOMS_AUTO:
        maengel.append(
            f"'interior.rooms' ist {raeume!r}. Belegt ist bei euch nur "
            f"'{INTERIOR_ROOMS_AUTO}' (seit 19.09.2026 gesendet, auf-31 R3, auf-91 V1); "
            f"welche Form ein Raum in einer Liste haette — Name, IFC-Kennung oder "
            f"Objekt —, ist nicht belegt, und wir raten sie nicht.")
        return None, None
    # Was bestellt war, wortgetreu — der Abholer vermerkt es am Kameraurteil.
    bestellt = {"rooms": INTERIOR_ROOMS_AUTO}
    if isinstance(kameras, list):
        warnungen.append(
            f"'interior' {{rooms: '{INTERIOR_ROOMS_AUTO}'}} kam zusammen mit "
            f"{len(kameras)} benannten Kamera(s). Nach eurer Antwort (auf-91 V1/V2) sind "
            f"das die drueben abgeleiteten Standpunkte: Gerendert werden genau diese, und "
            f"wir rechnen KEINEN zweiten Innenstandpunkt dazu (auf-31 R6). Welche der "
            f"Kameras innen steht, sagt die Bestellung nicht.")
        return None, bestellt
    if fmt != "ifc":
        maengel.append(
            f"'interior' verlangt Raeume, und die gibt es nur in einer IFC — die "
            f"Bestellung traegt geometry.format {fmt or None!r}. Aus einer glb laesst sich "
            f"kein Raumbegriff gewinnen; ersatzweise aussen zu rendern waere ein anderes "
            f"Bild als das bestellte.")
        return None, None
    return {"raum": None, "art": _raumkamera.ART_FRONTAL, "bestellt": bestellt}, bestellt


def _block(fremd: dict, name: str, maengel: list) -> dict:
    """Ein Unterblock der Bestellung — ``{}``, wenn er fehlt, und ein Mangel, wenn er
    da ist und kein Block ist (23.09.2026, siehe :func:`lies_szene`)."""
    inhalt = fremd.get(name)
    if inhalt is None:
        return {}
    if not isinstance(inhalt, dict):
        maengel.append(
            f"'{name}' ist {type(inhalt).__name__} ({inhalt!r}) und kein Block. Was "
            f"darin bestellt sein sollte, raten wir nicht; gerechnet wuerde sonst mit "
            f"den Vorgaben, und das waere nicht die Bestellung.")
        return {}
    return inhalt


#: Der Satz, wenn eine Bestellung weder Geometrie noch eine Grundlage nennt. Der Anfang ist der
#: Wortlaut von vor dem 21.10.2026 — er steht so in Abholer-Meldungen und Proben.
SATZ_OHNE_PFAD = ("render-scene ohne 'geometry.path' — es gibt nichts zu rendern. Ohne Modell "
                  "rechnet nur eine Variante einer fertigen Grundlage ('vis.grundlage', gl- und "
                  "16 Hexzeichen); diese Bestellung nennt keine.")


def hat_gueltige_grundlage(fremd) -> bool:
    """Traegt die Bestellung ``vis.grundlage`` mit einer gueltigen Kennung (``gl-`` + 16 hex)?"""
    vis = fremd.get("vis") if isinstance(fremd, dict) else None
    kennung = vis.get("grundlage") if isinstance(vis, dict) else None
    return isinstance(kennung, str) and bool(GRUNDLAGE_KENNUNG.match(kennung))


def _lies_grundlage_und_seed(vis: dict, skip, mit_skizze: bool, maengel: list,
                             endgueltig: list | None = None):
    """``(grundlage, seed)`` aus ``vis`` — beide ``None``, wenn nicht bestellt oder mangelhaft.

    Was nicht stimmt, wird als Mangel gemeldet und NICHT geraten: Eine falsch geschriebene
    Kennung als «keine Grundlage» zu lesen, hiesse still Blender neu rechnen — genau der
    Fehler, gegen den Nr. 85 antritt.
    """
    grundlage = vis.get("grundlage") if isinstance(vis, dict) else None
    if grundlage is not None and not (isinstance(grundlage, str)
                                      and GRUNDLAGE_KENNUNG.match(grundlage)):
        maengel.append(f"'vis.grundlage' ist {grundlage!r}. Erwartet ist die Kennung, die "
                       f"ein frueherer Lauf als grundlage.id gemeldet hat (gl- und 16 "
                       f"Hexzeichen).")
        grundlage = None
    seed = vis.get("seed") if isinstance(vis, dict) else None
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)
                             or not 0 <= seed <= SEED_HOECHSTENS):
        maengel.append(f"'vis.seed' ist {seed!r}. Erwartet ist eine ganze Zahl von 0 bis "
                       f"{SEED_HOECHSTENS}.")
        seed = None
    # WIDERSPRUECHE SIND ENDGUELTIG (auf-20261020-290, Befund 5): Sie stehen in der Szene,
    # und die aendert sich nicht durch Warten — darum zusaetzlich in `endgueltig`, damit der
    # Abholer den Auftrag mit Satz beendet, statt ihn alle 30 s neu zu lesen.
    widerspruch = []
    if grundlage is not None and skip:
        widerspruch.append("'vis.grundlage' und 'vis.skip' zugleich: Die Grundlage ist schon "
                           "gerechnet — ohne KI-Schritt entstuende nichts Neues.")
    if grundlage is not None and mit_skizze:
        widerspruch.append("'vis.grundlage' und 'skizze' zugleich: Die Skizze fuehrt ihr Bild "
                           "selbst und rechnet keine Blender-Grundlage.")
    maengel.extend(widerspruch)
    if endgueltig is not None:
        endgueltig.extend(widerspruch)
    return grundlage, seed


def _lies_guete(vis: dict, skip, maengel: list, endgueltig: list | None = None):
    """``vis.guete`` — ``'vorschau'``, ``'voll'`` oder ``None`` (nicht bestellt, gilt «voll»).

    Owner-Entscheid 104 (20.10.2026): Schalter «Güte: Vorschau | Voll» am Render-Knoten. Ein
    unbekannter Wert wird als Mangel gemeldet und **nicht** als «voll» gelesen — eine
    vertippte Vorschau, die still neun Minuten rechnet, wäre genau der Fehler, den der
    Schalter beheben soll. Zusammen mit ``vis.skip: true`` ist jede Güte ein Mangel: «nur
    Grundlage» rechnet kein KI-Bild, und eine Güte ohne KI-Bild bestellt nichts.
    """
    guete = vis.get("guete") if isinstance(vis, dict) else None
    if guete is None:
        return None
    if guete not in GUETEN:
        maengel.append(f"'vis.guete' ist {guete!r}. Erwartet ist 'vorschau' oder 'voll' "
                       f"(oder das Feld weglassen: dann gilt 'voll').")
        return None
    if skip:
        satz = (f"'vis.guete' ({guete!r}) und 'vis.skip' zugleich: «Nur Grundlage» "
                f"rechnet kein KI-Bild — eine Güte dafuer bestellt nichts.")
        maengel.append(satz)
        # Ein Widerspruch der Bestellung — endgueltig, siehe `_lies_grundlage_und_seed`.
        if endgueltig is not None:
            endgueltig.append(satz)
    return guete


def _gesetzt(block: dict, name: str) -> bool:
    """Vorhanden und nicht ``null`` — dieselbe Regel wie :func:`wert_oder`."""
    return isinstance(block, dict) and block.get(name) is not None


def _bereichszahl(block: dict, name: str, pfad: str, lo, hi, vorgabe, maengel: list):
    """Eine Kommazahl im Bereich ``lo..hi`` — die Vorgabe, wenn sie fehlt; ``None`` + Mangel,
    wenn sie nicht stimmt."""
    if not _gesetzt(block, name):
        return vorgabe
    zahl, satz = lies_zahl(block[name], pfad, ganzzahlig=False, mindestens=lo, hoechstens=hi)
    if satz:
        maengel.append(satz)
        return None
    return float(zahl)


def umgebung_aus_szene(roh, *, guete=None, grundlage=None, ordner=None) -> dict | None:
    """``render.environment`` → ``{umgebung, datei, maengel, endgueltig, fehlt}`` — oder ``None``.

    **Seit dem 20.10.2026** (Entscheide 107, 110, 113; Vertrag mit dem Integrator). Das Feld
    stand bis dahin in :data:`ABGEWIESENE_FELDER`.

    * ``umgebung`` — was gerechnet wird, **mit den Vorgaben des Heim-PC** (der Vertrag hat
      keine): ``{preset, hdri, intensitaet, rotationGrad}``; ``vorgaben`` daneben nennt die
      Felder, die der Heim-PC gesetzt hat. Ohne Pfad; diese
      Form geht in ``GRUNDLAGE_MUSS_PASSEN`` und ins Ergebnis (``angewandt.environment``).
    * ``datei`` — das Himmelsbild am Rechner aus :func:`aiimaging.stimmung.himmel_datei`
      (2k bei der Vorschau, sonst 4k). ``None`` bei ``vis.grundlage``: Dann rechnet Blender
      nicht, und das Bild wird nicht gebraucht.
    * ``fehlt`` — der Satz mit dem Namen, wenn das Bild fehlt (Entscheid 113). Er steht auch
      in ``maengel`` und ``endgueltig``: Der Auftrag endet mit Satz, und der Abholer legt ein
      Ergebnis mit ``lieferstatus_grund`` daneben.
    """
    if roh is None:
        return None
    maengel: list[str] = []
    endgueltig: list[str] = []
    antwort = {"umgebung": None, "datei": None, "maengel": maengel, "endgueltig": endgueltig,
               "fehlt": None}
    if not isinstance(roh, dict):
        maengel.append(f"'render.environment' ist {roh!r} und kein Block {{preset, hdri?, "
                       f"intensitaet?, rotationGrad?}}.")
        return antwort
    fremd = sorted(k for k in roh if k not in UMGEBUNG_FELDER)
    if fremd:
        maengel.append(f"Unbekannte Felder in 'render.environment': {', '.join(fremd)}. "
                       f"Bekannt sind {', '.join(UMGEBUNG_FELDER)}.")
    preset = roh.get("preset")
    if preset not in _stimmung.PRESETS:
        maengel.append(f"'render.environment.preset' ist {preset!r}. Erwartet ist eine der "
                       f"acht Stimmungen: {', '.join(_stimmung.PRESETS)}.")
        return antwort
    hdri = roh.get("hdri")
    vorgabe = hdri is None
    if vorgabe:
        hdri = _stimmung.STIMMUNGEN[preset]["hdri"]
    elif not (isinstance(hdri, str) and _stimmung.HDRI_MUSTER.match(hdri)):
        maengel.append(f"'render.environment.hdri' ist {hdri!r}. Erwartet ist der Namensstamm "
                       f"eines Himmelsbilds (a-z, 0-9, _; hoechstens 64 Zeichen), nie ein Pfad.")
        return antwort
    # Die Vorgabe JE STIMMUNG (auf-20261020-292): `stimmung.STIMMUNGEN[preset]['staerke']`.
    staerke = _bereichszahl(roh, "intensitaet", "render.environment.intensitaet", 0, 10,
                            _stimmung.vorgabe_staerke(preset), maengel)
    drehung = _bereichszahl(roh, "rotationGrad", "render.environment.rotationGrad", 0, 360,
                            _stimmung.VORGABE_DREHUNG_GRAD, maengel)
    if staerke is None or drehung is None:
        return antwort
    antwort["umgebung"] = {"preset": preset, "hdri": hdri, "intensitaet": staerke,
                           "rotationGrad": drehung}
    # Welche Werte der Heim-PC gesetzt hat — getrennt von `umgebung`, damit eine Bestellung
    # mit ausdruecklicher Vorgabe und eine ohne dieselbe Grundlage treffen.
    antwort["vorgaben"] = tuple(f for f in ("hdri", "intensitaet", "rotationGrad")
                                if not _gesetzt(roh, f))
    if grundlage is None and not maengel:
        datei = _stimmung.himmel_datei(preset, hdri, guete=guete, ordner=ordner)
        antwort["datei"] = datei
        if datei["satz"]:
            antwort["fehlt"] = datei["satz"]
            maengel.append(datei["satz"])
            endgueltig.append(datei["satz"])
    return antwort


#: Der Anfang des Satzes, wenn eine Variante ihre eigene Stimmung bekommt (N6, 22.10.2026).
SATZ_STIMMUNG_DER_VARIANTE = "STIMMUNG DER VARIANTE"


def stimmung_der_variante(prompt_en: str, environment, grundlage, *,
                          prompt_original: str | None = None,
                          licht_der_grundlage: str | None = None) -> dict | None:
    """Die Stimmung einer Variante, wenn sie NICHT die des Lichts ist — sonst ``None`` (N6).

    **Anlass (Mac-Demolauf 22.10.2026, N6):** Die Variante «Mittag» rechnete auf dem
    Abend-Grundbild und kam als blaue Nachtstimmung zurück. «Umriss halten» (M2, Entscheid
    126) hält ausserhalb des Hauses das Cycles-Bild der Grundlage fest — Himmel und Boden der
    ANDEREN Stimmung. Und wo die Bestellung ein Licht trägt, nahm der Heim-PC den Satz der
    Variante still aus dem Prompt und setzte den des Lichts (auf-20261021-306, B2) — aus
    «Mittag» wurde wortlos «Abend».

    Die Stimmung der Variante ist zuerst der **ganze Satz** einer Stimmung aus der Tabelle im
    (übersetzten) Prompt — so legen ihn der Stimmung-Knoten und der Varianten-Knoten hinein
    (:func:`aiimaging.stimmung.ohne_stimmungssaetze`). **Seit Befund 340 (22.10.2026)** zählt
    bei einer Variante (``grundlage`` bestellt) mit bestelltem Licht und ohne ganzen Satz auch
    das **Stimmungswort** (:func:`aiimaging.stimmung.stimmungen_im_text`, englisch aus dem
    Glossar, deutsch aus dem Original): «Abendstimmung» allein, «evening mood». Ohne Grundlage
    bleibt es beim ganzen Satz — dort hält kein fremdes Grundbild eine andere Stimmung fest —,
    ebenso ohne bestelltes Licht: «overcast sky» in einem freien Prompt ist dann ein Wort, keine
    Bestellung. Die Regel:

    * Genau **eine** Stimmung im Prompt, und sie ist nicht die des Lichts
      (``render.environment.preset``) → das Licht folgt der Variante: Blender rechnet mit
      ihrem Himmelsbild, und eine bestellte Grundlage (``vis.grundlage``) wird **nicht**
      wiederverwendet, sondern für diese Stimmung neu gerechnet. Eine Variante darf Himmel
      und Hintergrund einer anderen Stimmung nicht festhalten.
    * Ohne Licht in der Bestellung und ohne Grundlage bleibt es wie bisher: Das Cycles-Bild
      ist das eigene, ohne Stimmung (der ruhige Verlauf) — es gehört zu keiner anderen.
    * Kein Satz und kein Wort, mehrere Stimmungen, die des Lichts oder die des Gipsmodells
      («weiss») → ``None``, alles wie bisher.

    Rückgabe: ``{preset, licht_bestellt, licht_der_grundlage, grundlage_verworfen, quelle,
    satz}`` — ``quelle`` ist :data:`STIMMUNG_QUELLE_SATZ` oder
    :data:`STIMMUNG_QUELLE_WORT`. ``licht_der_grundlage`` ist die Stimmung, mit der die
    Grundlage gerechnet ist, wenn der Aufrufer sie kennt (``lies_szene`` aus
    ``umgebung_der_grundlage``) — sonst ``None``. Bis Ergebnis auf-20261022-342 (f) stand hier
    immer ``None``, auch wenn die verworfene Grundlage nachweislich mit «Mittag» gerechnet war.
    """
    from . import stimmung as _stimmung  # noqa: PLC0415
    rest, im_prompt = _stimmung.ohne_stimmungssaetze(prompt_en or "")
    quelle = STIMMUNG_QUELLE_SATZ
    if not im_prompt and grundlage is not None and environment is not None:
        # DAS STIMMUNGSWORT (Befund 340): nur fuer eine Variante MIT bestelltem Licht, nur ohne
        # ganzen Satz. Ohne Licht bleibt ein Wort ein Wort («overcast sky» in einem Prompt auf
        # einer Grundlage ohne Stimmung rechnet kein neues Grundbild).
        im_prompt = _stimmung.stimmungen_im_text(rest, prompt_original)
        quelle = STIMMUNG_QUELLE_WORT
    if len(im_prompt) != 1:
        return None
    variante = im_prompt[0]
    if environment is None:
        licht = None
    elif isinstance(environment, dict) and environment.get("preset") in _stimmung.PRESETS:
        licht = environment["preset"]
    else:
        # Ein Licht, das sich nicht lesen laesst, meldet `umgebung_aus_szene` als Mangel.
        return None
    if variante == licht or (licht is None and grundlage is None):
        return None
    if variante == _stimmung.PRESET_WEISS:
        # Das Gipsmodell ist keine Lichtstimmung: Es macht alle Oberflaechen zu Gips und
        # widerspricht gewaehlten Materialien (endgueltiger Mangel). Nicht still dahin wechseln.
        return None
    name = _stimmung.STIMMUNGEN[variante]["label"]
    licht_name = _stimmung.STIMMUNGEN[licht]["label"] if licht else "ohne Stimmung"
    satz = (f"{SATZ_STIMMUNG_DER_VARIANTE}: Der Prompt bestellt «{name}», das Licht der "
            f"Bestellung ist «{licht_name}». Gerechnet wird «{name}» mit eigenem Himmelsbild")
    if grundlage is not None:
        satz += (f", auf einer eigenen Grundlage — die Grundlage {grundlage} ist mit "
                 f"«{licht_name}» gerechnet, und «Umriss halten» hielte deren Himmel und Boden "
                 f"fest. Dafür rechnet Blender neu (länger als eine Variante)")
    satz += ". (N6, Mac-Demolauf 22.10.2026)"
    return {"preset": variante, "licht_bestellt": licht,
            "licht_der_grundlage": licht_der_grundlage if grundlage is not None else None,
            "grundlage_verworfen": grundlage, "quelle": quelle, "satz": satz}


#: Woher die Stimmung einer Variante kam (``stimmung_der_variante.quelle``, Befund 340).
STIMMUNG_QUELLE_SATZ = "prompt_satz"      # der ganze Satz der Tabelle im Prompt (N6)
STIMMUNG_QUELLE_WORT = "prompt_wort"      # nur das Stimmungswort («Abendstimmung»)
STIMMUNG_QUELLE_LICHT = "licht"           # das bestellte Licht selbst weicht von der Grundlage ab

#: Steht fuer «die Stimmung der Grundlage ist hier nicht bekannt» — dann prueft erst der
#: Abholer (`abholer.lies_grundlage`), wie bisher.
UMGEBUNG_UNBEKANNT = object()


def licht_der_variante(environment, umgebung_der_grundlage, grundlage) -> dict | None:
    """Das bestellte Licht einer Variante, wenn es NICHT das ihrer Grundlage ist (Befund 340).

    **Anlass (Ergebnis auf-20261022-340, demo-kritisch):** Der Mac bestellte die Variante
    «Licht abend» auf einer Mittag-Grundlage — ``render.environment.preset`` «abend», Prompt
    «Abendstimmung, warmes Licht, …». N6 (:func:`stimmung_der_variante`) sah im Prompt die
    Stimmung des Lichts und also nichts Abweichendes; die Grundlagenprüfung sah «Stimmung
    weicht ab» und wies mit 409 ab. Es entstand kein Auftrag. Wie bei N6 und beim Stoff
    (:func:`material_der_variante`) gilt jetzt: Die Grundlage wird verworfen und mit dem
    bestellten Licht neu gerechnet — gleiches Modell, gleiche Kamera, gleiche Werte sonst.

    ``umgebung_der_grundlage`` ist die gelesene Stimmung der Grundlage (``None``: ohne
    Stimmung gerechnet). Verglichen wird die gelesene Form beider (Himmelsbild, Stärke,
    Drehung samt Vorgaben). ``None``, wenn kein Licht bestellt ist (eine Variante ohne Licht
    bleibt, was sie war), wenn es sich nicht lesen lässt (ein Mangel von
    :func:`umgebung_aus_szene`), oder wenn es dem der Grundlage gleicht.

    Rückgabe wie :func:`stimmung_der_variante`, ``quelle`` :data:`STIMMUNG_QUELLE_LICHT`.
    """
    if grundlage is None or environment is None:
        return None
    import json  # noqa: PLC0415
    from . import stimmung as _stimmung  # noqa: PLC0415
    block = umgebung_aus_szene(environment, grundlage=grundlage)
    if block is None or block["maengel"] or block["umgebung"] is None:
        return None
    jetzt = block["umgebung"]

    def form(wert):
        return json.loads(json.dumps(wert, sort_keys=True, default=str))

    if form(jetzt) == form(umgebung_der_grundlage):
        return None
    preset = jetzt["preset"]
    vorher = (umgebung_der_grundlage or {}).get("preset") if isinstance(
        umgebung_der_grundlage, dict) else None
    name = _stimmung.STIMMUNGEN[preset]["label"]
    vorher_name = (_stimmung.STIMMUNGEN[vorher]["label"] if vorher in _stimmung.STIMMUNGEN
                   else "ohne Stimmung")
    if vorher == preset:
        was = (f"mit anderen Lichtwerten als die Grundlage {grundlage} (Himmelsbild, Stärke "
               f"oder Drehung)")
    else:
        was = f"anders als die Grundlage {grundlage}, die mit «{vorher_name}» gerechnet ist"
    satz = (f"{SATZ_STIMMUNG_DER_VARIANTE}: Bestellt ist das Licht «{name}», {was}. Gerechnet "
            f"wird «{name}» mit eigenem Himmelsbild, auf einer eigenen Grundlage — gleiches "
            f"Modell, gleiche Kamera; «Umriss halten» hielte sonst Himmel und Boden der "
            f"Grundlage fest. Dafür rechnet Blender neu (länger als eine Variante). "
            f"(Befund 340)")
    return {"preset": preset, "licht_bestellt": preset, "licht_der_grundlage": vorher,
            "grundlage_verworfen": grundlage, "quelle": STIMMUNG_QUELLE_LICHT, "satz": satz}


#: Der Anfang des Satzes, wenn eine Variante einen anderen Fassadenstoff bestellt (Befund 337).
SATZ_MATERIAL_DER_VARIANTE = "MATERIAL DER VARIANTE"

#: Wie die Ersetzung lief: die Materialwahl der Fassade (Blender rechnet eine neue Grundlage)
#: oder nur der Prompt (kein Material der Bibliothek für diesen Stoff, z. B. Glas, Metall).
ERSETZUNG_MATERIALWAHL = "materialwahl"
ERSETZUNG_NUR_PROMPT = "nur_prompt"


def material_der_variante(prompt_en: str, materialien_roh, grundlage, *,
                          environment=None) -> dict | None:
    """Der Fassadenstoff einer Variante, wenn er NICHT der der Materialwahl ist (Befund 337).

    **Anlass (Ergebnis auf-20261022-337):** Die Variante «Fassade aus Sichtbeton» auf der
    Grundlage mit Holzlattung kam in keinem Lauf. Der Satz «Material vorne» (Entscheid 126)
    stellte den Stoff der MATERIALWAHL nach vorne («monolithic spruce timber battens
    building …»), und das Grundbild trug die Holztextur — mit Bildeingang 0,5 malt die KI den
    Stoff kaum um. Wie bei der Stimmung (N6): Die Variante braucht ihr eigenes Grundbild.

    Nur für eine **Variante** (``vis.grundlage`` bestellt). Gesucht wird im (übersetzten)
    Prompt ohne die Stimmungssätze (:func:`aiimaging.materialwahl.stoff_wunsch`). Die Regel:

    * Genau **eine** Stofffamilie für die Fassade, und sie ist nicht die der gewählten
      Fassade → mit Material der Bibliothek: ``render.materialien.fassade`` wird dieses
      Material (Vorgaben für Massstab, Drehung, Relief; keine Tönung), die Grundlage wird
      **nicht** wiederverwendet, sondern neu gerechnet (``ersetzung`` «materialwahl»). Ohne
      Material der Bibliothek (Glas, Metall): nur der Prompt — der Wunschstoff steht vorne,
      der Satz der gewählten Fassade fällt weg, das Grundbild bleibt (``nur_prompt``).
    * Dach, Fenster, Boden, übrige und Gelände bleiben, wie gewählt.
    * Derselbe Stoff wie gewählt, mehrere Familien, oder Gipsmodell («weiss») → keine
      Ersetzung (``ersetzung`` None, ``grund`` sagt warum); ohne Stoffwunsch → ``None``.

    Rückgabe: ``{wunsch, familie, id, vorher, ersetzung, grundlage_verworfen, grund, satz}``.
    """
    if grundlage is None:
        return None
    from . import stimmung as _stimmung  # noqa: PLC0415
    ohne, _ = _stimmung.ohne_stimmungssaetze(prompt_en or "")
    wuensche = _materialwahl.stoff_wunsch(ohne)
    if not wuensche:
        return None
    vorher = None
    if isinstance(materialien_roh, dict) and isinstance(materialien_roh.get("fassade"), dict):
        vorher = materialien_roh["fassade"].get("id")
    erster = wuensche[0]
    antwort = {"wunsch": erster["wort"], "familie": erster["familie"], "id": erster["id"],
               "vorher": vorher, "ersetzung": None, "grundlage_verworfen": None,
               "grund": None, "satz": None}
    familien = list(dict.fromkeys(w["familie"] for w in wuensche))
    if len(familien) > 1:
        antwort["grund"] = (f"mehrere Stoffe fuer die Fassade ({', '.join(familien)}) — welcher "
                            f"gilt, wird nicht geraten")
        antwort["satz"] = (f"{SATZ_MATERIAL_DER_VARIANTE}: Der Prompt nennt mehrere Stoffe fuer "
                           f"die Fassade ({', '.join(w['wort'] for w in wuensche)}); die "
                           f"Materialwahl bleibt. (Befund 337)")
        return antwort
    if materialien_roh is not None and not isinstance(materialien_roh, dict):
        return None                       # ein Mangel von `materialien_aus_szene`
    if vorher is not None and _materialwahl.FAMILIE.get(vorher) == erster["familie"]:
        antwort["grund"] = "derselbe Stoff wie die gewaehlte Fassade"
        return antwort
    vorher_name = (_materialwahl.BIBLIOTHEK.get(vorher, {}).get("label") or vorher
                   if vorher else "das Material der Datei")
    if erster["id"] is None:
        antwort["ersetzung"] = ERSETZUNG_NUR_PROMPT
        antwort["grund"] = "kein Material der Bibliothek fuer diesen Stoff"
        antwort["satz"] = (f"{SATZ_MATERIAL_DER_VARIANTE}: Der Prompt bestellt die Fassade aus "
                           f"«{erster['wort']}», gewaehlt ist {vorher_name}. Fuer diesen Stoff "
                           f"gibt es kein Material der Bibliothek — er steht vorne im Prompt, "
                           f"aber das Grundbild bleibt (Cycles rechnet weiter {vorher_name}). "
                           f"(Befund 337)")
        return antwort
    preset = environment.get("preset") if isinstance(environment, dict) else None
    if preset == _stimmung.PRESET_WEISS:
        antwort["grund"] = "Gipsmodell (Stimmung 'weiss') — es zeigt keine Materialien"
        return antwort
    label = _materialwahl.BIBLIOTHEK[erster["id"]]["label"]
    antwort["ersetzung"] = ERSETZUNG_MATERIALWAHL
    antwort["grundlage_verworfen"] = grundlage
    antwort["satz"] = (f"{SATZ_MATERIAL_DER_VARIANTE}: Der Prompt bestellt die Fassade aus "
                       f"«{erster['wort']}», gewaehlt war {vorher_name}. Gerechnet wird die "
                       f"Fassade mit «{label}», auf einer eigenen Grundlage — die Grundlage "
                       f"{grundlage} traegt den alten Stoff im Grundbild. Dach, Fenster und "
                       f"Gelaende bleiben. Dafuer rechnet Blender neu (laenger als eine "
                       f"Variante). (Befund 337)")
    return antwort


def umgebung_der_variante(environment, variante: dict) -> dict:
    """``render.environment`` für die Stimmung der Variante — nur die Drehung bleibt.

    Himmelsbild und Stärke einer ausdrücklich bestellten Stimmung gehören zu IHR; die der
    Variante kommen aus ihrer Vorgabe (:data:`aiimaging.stimmung.STIMMUNGEN`).
    """
    neu = {"preset": variante["preset"]}
    if isinstance(environment, dict) and _gesetzt(environment, "rotationGrad"):
        neu["rotationGrad"] = environment["rotationGrad"]
    return neu


#: Die Felder einer MaterialWahl (Vertrag 20.10.2026) und ihrer Toenung.
MATERIALWAHL_FELDER = ("id", "massstab_m", "drehungGrad", "relief", "toenung")
TOENUNG_FELDER = ("farbe", "staerke")


def materialien_aus_szene(roh, *, guete=None, grundlage=None, ordner=None) -> dict | None:
    """``render.materialien`` → ``{materialien, dateien, vorgaben, maengel, endgueltig, fehlt}``.

    **Seit dem 20.10.2026** (Knoten «Material», Entscheide 107/111/113). ``materialien`` ist
    je bestellter Art die Wahl mit den Vorgaben des Heim-PC (Massstab 1 m, Drehung 0, Relief
    0,6) — ohne Pfad, so geht sie in ``GRUNDLAGE_MUSS_PASSEN`` und ins Ergebnis. ``dateien``
    traegt je Art die Karten am Rechner (:func:`aiimaging.materialwahl.texturen`: 1K bei der
    Vorschau, sonst 2K) und nie ins Ergebnis; ``None`` bei ``vis.grundlage`` (kein Blender).
    Ein leeres ``{}`` bestellt nichts und wird abgewiesen (Vertrag). Unbekannte id und
    fehlende Textur enden mit Satz (``endgueltig``), die fehlende Textur dazu mit ihrem Namen
    unter ``fehlt`` fuer ``lieferstatus_grund`` (Entscheid 113).
    """
    if roh is None:
        return None
    maengel: list[str] = []
    endgueltig: list[str] = []
    fehlt: list[str] = []
    antwort = {"materialien": None, "dateien": None, "vorgaben": {}, "maengel": maengel,
               "endgueltig": endgueltig, "fehlt": fehlt}
    if not isinstance(roh, dict):
        maengel.append(f"'render.materialien' ist {roh!r} und kein Block {{fassade?, dach?, "
                       f"fenster?, boden?, uebrige?}}.")
        return antwort
    if not roh:
        satz = ("'render.materialien' ist leer ({}) — es bestellt nichts. Ohne Material "
                "das Feld weglassen.")
        maengel.append(satz)
        endgueltig.append(satz)
        return antwort
    fremd = sorted(k for k in roh if k not in _materialwahl.ARTEN)
    if fremd:
        maengel.append(f"Unbekannte Arten in 'render.materialien': {', '.join(fremd)}. "
                       f"Bekannt sind {', '.join(_materialwahl.ARTEN)}.")
    gewaehlt: dict = {}
    vorgaben: dict = {}
    for art in _materialwahl.ARTEN:
        wahl = roh.get(art)
        if wahl is None:
            continue
        pfad = f"render.materialien.{art}"
        if not isinstance(wahl, dict):
            maengel.append(f"'{pfad}' ist {wahl!r} und keine MaterialWahl {{id, ...}}.")
            continue
        unbekannt = sorted(k for k in wahl if k not in MATERIALWAHL_FELDER)
        if unbekannt:
            maengel.append(f"Unbekannte Felder in '{pfad}': {', '.join(unbekannt)}.")
        kennung = wahl.get("id")
        if not (isinstance(kennung, str) and _materialwahl.ID_MUSTER.match(kennung)):
            maengel.append(f"'{pfad}.id' ist {kennung!r}. Erwartet ist die Kennung eines "
                           f"Materials der Bibliothek (a-z, 0-9, -; hoechstens 48 Zeichen).")
            continue
        if kennung not in _materialwahl.BIBLIOTHEK:
            satz = (f"Material '{kennung}' ({art}) ist nicht in der Bibliothek des Heim-PC. "
                    f"Bekannt: {', '.join(_materialwahl.BIBLIOTHEK)}.")
            maengel.append(satz)
            endgueltig.append(satz)
            # AUCH INS ERGEBNIS (auf-20261020-292, B8): Bis dahin endete eine unbekannte id
            # nur am Laufzettel, ohne render-result.json — anders als eine fehlende Textur
            # oder ein fehlendes Himmelsbild. Die Oberflaeche liest `lieferstatus_grund`.
            if satz not in fehlt:
                fehlt.append(satz)
            continue
        massstab = _bereichszahl(wahl, "massstab_m", f"{pfad}.massstab_m", 0.05, 20,
                                 _materialwahl.VORGABE_MASSSTAB_M, maengel)
        drehung = _bereichszahl(wahl, "drehungGrad", f"{pfad}.drehungGrad", 0, 360,
                                _materialwahl.VORGABE_DREHUNG_GRAD, maengel)
        relief = _bereichszahl(wahl, "relief", f"{pfad}.relief", 0, 1,
                               _materialwahl.VORGABE_RELIEF, maengel)
        toenung = None
        if _gesetzt(wahl, "toenung"):
            t = wahl["toenung"]
            if not isinstance(t, dict) or sorted(k for k in t if k not in TOENUNG_FELDER):
                maengel.append(f"'{pfad}.toenung' ist {t!r}. Erwartet ist {{farbe: '#rrggbb', "
                               f"staerke: 0..1}}.")
            elif not (isinstance(t.get("farbe"), str)
                      and _materialwahl.FARB_MUSTER.match(t["farbe"])):
                maengel.append(f"'{pfad}.toenung.farbe' ist {t.get('farbe')!r}. Erwartet ist "
                               f"'#rrggbb'.")
            else:
                if not _gesetzt(t, "staerke"):
                    maengel.append(f"'{pfad}.toenung' ohne 'staerke'.")
                staerke = _bereichszahl(t, "staerke", f"{pfad}.toenung.staerke", 0, 1, None,
                                        maengel)
                if staerke is not None:
                    toenung = {"farbe": t["farbe"].lower(), "staerke": staerke}
        if None in (massstab, drehung, relief):
            continue
        gewaehlt[art] = {"id": kennung, "massstab_m": massstab, "drehungGrad": drehung,
                         "relief": relief, "toenung": toenung}
        vorgaben[art] = [f for f in ("massstab_m", "drehungGrad", "relief")
                         if not _gesetzt(wahl, f)]
    if maengel:
        return antwort
    antwort["materialien"] = gewaehlt
    antwort["vorgaben"] = vorgaben
    if grundlage is None:
        dateien = {}
        for art, wahl in gewaehlt.items():
            gefunden = _materialwahl.texturen(wahl["id"], guete=guete, ordner=ordner)
            if gefunden["satz"]:
                if gefunden["satz"] not in fehlt:
                    fehlt.append(gefunden["satz"])
                    maengel.append(gefunden["satz"])
                    endgueltig.append(gefunden["satz"])
                continue
            dateien[art] = gefunden
        antwort["dateien"] = dateien
    return antwort


#: Die Vorgaben des Heim-PC fuer ``cameras_auto`` (der Vertrag hat keine). Augenhoehe und
#: Brennweite aus :mod:`aiimaging.kameras`, «Haus fuellt» 0.70 (Entscheid 113 = gemessenes
#: ``kameras.DECKUNGSGRAD``), Perspektive senkrecht (Entscheid 109 C).
KAMERAS_AUTO_BRENNWEITEN = (24, 35, 50)
KAMERAS_AUTO_HOECHSTENS = 8


def kameras_auto_aus_szene(roh, *, maengel: list, endgueltig: list | None = None) -> dict | None:
    """``cameras_auto`` → ``{richtungen, augenhoehe_m, brennweite_mm, abstand, perspektive,
    vorgaben}`` — oder ``None`` (nicht bestellt bzw. mangelhaft, Satz in ``maengel``).

    **Seit dem 20.10.2026** (Knoten «Kamera», Entscheide 109/113; Vertrag mit dem
    Integrator). Bis dahin galten Richtungen, Augenhoehe, Brennweite und Deckungsgrad nur als
    Einstellungen des ganzen Abholers. ``abstand`` ist ``{art: 'auto', fuellt}`` oder ``{art:
    'fest', meter}``; ``vorgaben`` nennt, was der Heim-PC gesetzt hat. Dieselbe Pruefung
    nimmt ``knotenweg.standpunkte_abfrage`` fuer die Vorschau der Kegel.
    """
    if roh is None:
        return None
    vorher = len(maengel)
    if not isinstance(roh, dict):
        maengel.append(f"'cameras_auto' ist {roh!r} und kein Block {{richtungen, ...}}.")
        return None
    richtungen = roh.get("richtungen")
    # DEUTSCHE KUERZEL ALS GLEICHWORT (auf-20261021-314, B2): «nNO» heisst «nNE».
    umgedeutet = {}
    if isinstance(richtungen, list):
        gelesen = []
        for r in richtungen:
            neu, um = _kameras.kuerzel_lesen(r)
            if um:
                umgedeutet[r] = neu
            gelesen.append(neu)
        richtungen = gelesen
    if (not isinstance(richtungen, list) or not richtungen
            or len(richtungen) > KAMERAS_AUTO_HOECHSTENS
            or any(r not in _kameras.RICHTUNGEN for r in richtungen)
            or len(set(richtungen)) != len(richtungen)):
        satz = (f"'cameras_auto.richtungen' ist {roh.get('richtungen')!r}. Erwartet sind 1 bis "
                f"{KAMERAS_AUTO_HOECHSTENS} verschiedene Kuerzel aus "
                f"{', '.join(_kameras.RICHTUNGSFOLGE)} (deutsch auch "
                f"{', '.join(_kameras.GLEICHWORTE_DEUTSCH)}).")
        maengel.append(satz)
        # ENDGUELTIG (B2): Ein unbekanntes Kuerzel wird nicht von selbst richtig — der Auftrag
        # endet mit diesem Satz, statt still «queued» zu haengen, bis jemand abbricht.
        if endgueltig is not None:
            endgueltig.append(satz)
    auge = _bereichszahl(roh, "augenhoehe_m", "cameras_auto.augenhoehe_m", 0.5, 50,
                         _kameras.AUGENHOEHE_M, maengel)
    brennweite = roh.get("brennweite_mm")
    if brennweite is None:
        brennweite = _kameras.BRENNWEITE_MM
    elif (isinstance(brennweite, bool) or not isinstance(brennweite, (int, float))
          or brennweite not in KAMERAS_AUTO_BRENNWEITEN):
        maengel.append(f"'cameras_auto.brennweite_mm' ist {brennweite!r}. Erwartet ist "
                       f"24, 35 oder 50.")
    abstand_roh = roh.get("abstand")
    abstand = {"art": "auto", "fuellt": _kameras.DECKUNGSGRAD}
    if abstand_roh is not None:
        art = abstand_roh.get("art") if isinstance(abstand_roh, dict) else None
        if art == "auto":
            fremd = sorted(k for k in abstand_roh if k not in ("art", "fuellt"))
            fuellt = _bereichszahl(abstand_roh, "fuellt", "cameras_auto.abstand.fuellt",
                                   0.2, 0.95, _kameras.DECKUNGSGRAD, maengel)
            abstand = {"art": "auto", "fuellt": fuellt}
        elif art == "fest":
            fremd = sorted(k for k in abstand_roh if k not in ("art", "meter"))
            if not _gesetzt(abstand_roh, "meter"):
                maengel.append("'cameras_auto.abstand' {art: 'fest'} ohne 'meter'.")
                meter = None
            else:
                meter = _bereichszahl(abstand_roh, "meter", "cameras_auto.abstand.meter",
                                      2, 2000, None, maengel)
            abstand = {"art": "fest", "meter": meter}
        else:
            fremd = []
            maengel.append(f"'cameras_auto.abstand' ist {abstand_roh!r}. Erwartet ist "
                           f"{{art: 'auto', fuellt?}} oder {{art: 'fest', meter}}.")
        if fremd:
            maengel.append(f"Unbekannte Felder in 'cameras_auto.abstand': {', '.join(fremd)}.")
    perspektive = roh.get("perspektive")
    if perspektive is None:
        perspektive = PERSPEKTIVE_SENKRECHT
    elif perspektive not in PERSPEKTIVEN:
        maengel.append(f"'cameras_auto.perspektive' ist {perspektive!r}. Erwartet ist "
                       f"'senkrecht' oder 'frei'.")
    if len(maengel) > vorher:
        return None
    vorgaben = [f for f in ("augenhoehe_m", "brennweite_mm", "abstand", "perspektive")
                if not _gesetzt(roh, f)]
    if abstand["art"] == "auto" and not _gesetzt(abstand_roh or {}, "fuellt") \
            and "abstand" not in vorgaben:
        vorgaben.append("abstand.fuellt")
    aus = {"richtungen": list(richtungen), "augenhoehe_m": float(auge),
           "brennweite_mm": float(brennweite), "abstand": abstand,
           "perspektive": perspektive, "vorgaben": vorgaben}
    if umgedeutet:
        # steht so in `angewandt.cameras_auto` — das Ergebnis sagt, was gelesen wurde
        aus["umgedeutet"] = umgedeutet
    return aus


def kameras_auto_unvertraeglich(*, kameras, skizze, interior) -> list[str]:
    """Was mit ``cameras_auto`` nicht zusammengeht — je ein Satz (endgueltig).

    Vertrag: nur mit ``cameras === 'auto'`` (fehlend gilt als 'auto'), nicht mit ``skizze``
    oder ``interior``.
    """
    saetze = []
    if kameras != "auto":
        saetze.append("'cameras_auto' verlangt cameras: 'auto' (oder kein 'cameras') — mit "
                      "einer Kameraliste waere der Standpunkt zweimal bestellt.")
    if skizze is not None:
        saetze.append("'cameras_auto' und 'skizze' zugleich: Die Skizze fuehrt ihr Bild "
                      "selbst, es gibt keine Kamera zu rechnen.")
    if interior is not None:
        saetze.append("'cameras_auto' und 'interior' zugleich: Die Innenansicht rechnet ihren "
                      "Standpunkt aus den Raeumen.")
    return saetze


#: Das Gebäudewort, das vor den Prompt kommt, wenn sein **Bauteil leer** ist
#: (auf-20261021-309, B3). Nimmt :func:`stimmung.ohne_stimmungssaetze` den Satz des
#: Stimmungs-Knotens heraus und schrieb der Besteller sonst nichts, bestand der Prompt nur noch
#: aus dem Stimmungssatz: S1 «abend» zeigte eine Höhle mit einem Gefäss, S2 «nebel» ein
#: verschmiertes Gestell — nichts im Prompt sagte, dass ein Gebäude gemeint ist. Englisch, wie
#: alles, was das Bildmodell liest; der Stimmungssatz bleibt einmal dahinter.
GEBAEUDEWORT = "architectural building"


def zusatz_gebaeudewort(prompt_en: str) -> str | None:
    """:data:`GEBAEUDEWORT`, wenn der Bauteil des Prompts **leer** ist — sonst ``None``.

    Leer heisst: nach dem Herausnehmen der Stimmungssätze bleibt nichts als Leerzeichen und
    Kommas. Was der Besteller selbst schreibt, bleibt Wort für Wort und bekommt nichts dazu.
    """
    if (prompt_en or "").strip(" ,\t\n"):
        return None
    return GEBAEUDEWORT


#: Der Zusatz für den KI-Schritt, den ``vis.leerer_hintergrund: true`` an den Prompt hängt
#: (auf-20261021-296, N3). **Vorbereitet, nicht eingebaut — Vorgabe aus.** In 296 blieb nur
#: das Gipsmodell mit diesem Satz im Prompt im Umriss (``ausserhalb_umriss_anteil`` 0,0);
#: mittag mit Standardprompt baute auch bei ``faithful`` 1,0 über fast die ganze Breite
#: (1,01). Ob es am Satz liegt oder am Gipsmodell, misst auf-20261021-297 mit und ohne.
#: Ein Schalter von uns, kein Feld des Vertrags drüben: Wird er Vorgabe oder bestellbar über
#: die Knotenansicht, ist das eine Vertragsänderung (Integrator) und ein Knotenteil (beide
#: Programme).
ZUSATZ_LEERER_HINTERGRUND = "empty background, no other buildings"
#: Woran erkannt wird, dass der Prompt den Zusatz schon trägt (klein geschrieben).
ZUSATZ_LEERER_HINTERGRUND_MERKMALE = ("empty background", "no other buildings")


def zusatz_leerer_hintergrund(prompt_en: str) -> tuple[str | None, bool]:
    """``(satz, schon_da)`` — :data:`ZUSATZ_LEERER_HINTERGRUND`, wenn der Prompt ihn nicht trägt.

    Dieselbe Form wie ``stimmung.prompt_satz``: Trägt der (übersetzte) Prompt eines der
    Merkmale schon, wird nichts angefügt — sonst stünde es doppelt da.
    """
    text = (prompt_en or "").lower()
    if all(m in text for m in ZUSATZ_LEERER_HINTERGRUND_MERKMALE):
        return None, True
    return ZUSATZ_LEERER_HINTERGRUND, False


#: Der Satz von ``vis.glas_satz`` (Mac-Befund 23.10.2026, «haus-am-hang», auf-20261023-346):
#: Bei Bildeingang 0,5 malte die KI das schmale Fensterband im OG mit Lattung zu, und der
#: Prompt nannte vorne dreimal die Lattung («made entirely of …», «… on all exterior
#: surfaces») und nirgends Glas. Der Satz nennt das Glas als zweiten Stoff — **ohne
#: Bauteilwort** (``prompts.BAUTEILWOERTER``: «window», «windows»): Ein Satz «ribbon windows»
#: bestellte eine Form, und wo das Modell Lochfenster hat, malte die KI Bänder — der teuerste
#: Fehler dieses Projekts (ein Bauteil im Prompt, das die Geometrie nicht hat). Die Form
#: kommt aus dem Grundbild; der Satz sagt nur, dass Glas zum Haus gehört. **Nur mit Schalter**
#: (Vorgabe aus): ob er hilft, ist ungemessen.
GLAS_SATZ = "clear transparent glazing"
#: Woran erkannt wird, dass der Prompt den Satz schon trägt (klein geschrieben).
GLAS_SATZ_MERKMALE = ("glazing",)


def zusatz_glas(prompt_en: str) -> tuple[str | None, bool]:
    """``(satz, schon_da)`` — :data:`GLAS_SATZ`, wenn der Prompt ihn nicht schon trägt."""
    text = (prompt_en or "").lower()
    if all(m in text for m in GLAS_SATZ_MERKMALE):
        return None, True
    return GLAS_SATZ, False


def lies_glas_satz(vis: dict, *, skip, maengel: list, endgueltig: list) -> bool | None:
    """``vis.glas_satz`` (auf-20261023-346): true/false/null, **Vorgabe aus**.

    Mit ``true`` steht :data:`GLAS_SATZ` vorne im Prompt, direkt hinter dem Stoff von
    ``vis.material_vorne`` (ohne ihn ganz vorne). Ein Messschalter von uns, kein Feld des
    Vertrags. Mit «nur Grundlage» endgültiger Mangel wie bei ``vis.leerer_hintergrund``.
    ``None`` heisst: nicht gelesen (Mangel).
    """
    wert = wert_oder(vis, "glas_satz", False)
    if not isinstance(wert, bool):
        maengel.append(
            f"'vis.glas_satz' ist {wert!r}, erwartet war true, false oder null. Ein anderer "
            f"Wert laesst sich nicht deuten — als Text waere \"false\" wahr.")
        return None
    if wert and skip:
        satz = ("'vis.glas_satz' und 'vis.skip' zugleich: «Nur Grundlage» rechnet kein "
                "KI-Bild — ein Satz fuer den KI-Schritt bestellt nichts.")
        maengel.append(satz)
        endgueltig.append(satz)
    return wert


def lies_material_vorne_nennungen(vis: dict, *, maengel: list) -> int:
    """``vis.material_vorne_nennungen`` (auf-20261023-346): 1 bis 3 oder null — **Vorgabe 3**.

    Wie oft der Hauptstoff mit ``vis.material_vorne`` höchstens im ganzen Prompt steht
    (:data:`MATERIAL_VORNE_HOECHSTENS`). Mit 1 bleibt vorne nur «monolithic <Stoff>
    building»; «made entirely of …» und «… on all exterior surfaces», die einem Fensterband
    widersprechen, entfallen. Ein Messschalter von uns; ohne ihn ist der Prompt Wort für Wort
    derselbe. Ein anderer Wert ist ein Mangel, und es gilt die Vorgabe.
    """
    wert = wert_oder(vis, "material_vorne_nennungen", None)
    if wert is None:
        return MATERIAL_VORNE_HOECHSTENS
    if isinstance(wert, bool) or not isinstance(wert, int) \
            or not 1 <= wert <= MATERIAL_VORNE_HOECHSTENS:
        maengel.append(
            f"'vis.material_vorne_nennungen' ist {wert!r}, erwartet war eine ganze Zahl von 1 "
            f"bis {MATERIAL_VORNE_HOECHSTENS} oder null (Vorgabe {MATERIAL_VORNE_HOECHSTENS}).")
        return MATERIAL_VORNE_HOECHSTENS
    return wert


def lies_farbabgleich(vis: dict, *, skip, maengel: list, endgueltig: list) -> bool | None:
    """``vis.farbabgleich`` (Entscheid 117, D1): true/false/null, **Vorgabe aus**.

    Mit ``true`` gleicht der Heim-PC die Farben des KI-Bilds an das Cycles-Bild an
    (:mod:`aiimaging.farbabgleich`); nichts an der Form verschiebt sich. Ein Messschalter von
    uns, kein Feld des Vertrags. Mit «nur Grundlage» gibt es kein KI-Bild — endgültiger
    Mangel, wie bei ``vis.leerer_hintergrund``. ``None`` heisst: nicht gelesen (Mangel).
    """
    wert = wert_oder(vis, "farbabgleich", False)
    if not isinstance(wert, bool):
        maengel.append(
            f"'vis.farbabgleich' ist {wert!r}, erwartet war true, false oder null. Ein "
            f"anderer Wert laesst sich nicht deuten — als Text waere \"false\" wahr.")
        return None
    if wert and skip:
        satz = ("'vis.farbabgleich' und 'vis.skip' zugleich: «Nur Grundlage» rechnet kein "
                "KI-Bild — es gibt nichts abzugleichen.")
        maengel.append(satz)
        endgueltig.append(satz)
    return wert


#: Der kleinste und groesste Wert von ``vis.bildeingang`` (die Staerke, Entscheid 117).
BILDEINGANG_SPANNE = (0.05, 1.0)
#: Die Staerke der Vorgabe fuer ein ERSTES Bild ohne Grundlage (Entscheid 138, 22.10.2026; gemessen
#: auf-20261022-337) — seit Entscheid 149 nur noch dort.
BILDEINGANG_VORGABE = 0.5
#: **Die Staerke der Vorgabe fuer Varianten (Entscheid 149, 24.10.2026, Owner ueber die Zentrale nach
#: Messung auf-20261024-353, Option 1):** 0,7 mit «Umriss halten» im Lauf. 353: bis 0,7 halten Fenster
#: und Form an allen vier Kameras (Fenster >= 0,70, Deckung im Haus >= 0,36, kein Satz), es kommt mehr
#: Material an als mit 0,5; bei 0,8 kippt zuerst die Form. Eine Variante ist ein Auftrag auf einer
#: Grundlage (``vis.grundlage``, auch wenn sie wegen Stimmung oder Stoff neu gerechnet wird); ein
#: Auftrag ohne Grundlage (das erste Bild des Render-Knotens) behaelt :data:`BILDEINGANG_VORGABE`.
BILDEINGANG_VORGABE_VARIANTE = 0.7
#: **Entscheid 149, ergänzt (Owner über die Zentrale, 24.10.2026 abends):** die Stärke hängt am
#: Modell. Auf einem SITUATIONSMODELL (eine Anlage, dieselbe Regel wie die Vogelschau,
#: ``kameras.ist_situationsmodell``) rechnet eine Variante ohne eigene Stärke mit 0,5: Am
#: Wettbewerbsmodell löste 0,7 (Zelle B2C3, sSE, Umriss halten) das Hauptgebäude mit Hof in
#: grüne Flecken auf und die Halle in eine glatte Platte — bei «deckungsgleich» (Kanten-IoU
#: am Haus 0,256 gegen die Schwelle 0,25). Gesetzt erst im Abholer, wo Modell oder Grundlage
#: bekannt sind (:func:`bildeingang_fuer_situationsmodell`).
BILDEINGANG_VORGABE_SITUATION = 0.5
#: Die Herkunft, wenn die Vorgabe wegen des Situationsmodells gilt.
HERKUNFT_VORGABE_SITUATION = "vorgabe_situationsmodell"
#: Der Anfang des Satzes, wenn die Vorgabe wegen der Lizenz des Modells entfaellt (Entscheid 138).
SATZ_BILDEINGANG_LIZENZ = "OHNE BILDEINGANG (Entscheid 138)"


def lies_bildeingang(vis: dict, *, skip, guete, backbone_name,
                     maengel: list, endgueltig: list) -> float | None:
    """``vis.bildeingang`` (Entscheid 117, Variante A): eine Stärke, ``false`` oder null.

    **Seit Entscheid 138 (22.10.2026) Vorgabe** mit :data:`BILDEINGANG_VORGABE` (0,5), für
    Varianten seit Entscheid 149 :data:`BILDEINGANG_VORGABE_VARIANTE` (0,7) — eingesetzt von ``lies_szene`` über :data:`VARIANTEN_VORGABE`, nur wo
    :func:`varianten_vorgabe_entfaellt` nichts einwendet. ``false`` schaltet ab (ausdrücklich
    bestellt, kein Mangel); ``null`` oder fehlend heisst «Vorgabe».

    Mit einer Zahl in :data:`BILDEINGANG_SPANNE` geht das Cycles-Bild **zusätzlich** zur Tiefe
    ins Bildmodell — über den vorbereiteten, ungemessenen Weg des Eintrags
    (``Backbone.bildeingang_weg``). Die Stärke sagt, wie viel neu gemalt wird. Ein Messschalter
    von uns, kein Feld des Vertrags; bestellt nur über die Brücke mit eigener Szene.

    Endgültige Mängel (der Auftrag endet mit Satz): mit «nur Grundlage» (kein KI-Bild), mit
    der Vorschau (sie rechnet immer mit demselben Modell, Entscheid 104) und an einem Modell
    ohne vorbereiteten Weg. Ein Wert, der keine Zahl ist: Mangel, Rückgabe ``None``.
    """
    wert = wert_oder(vis, "bildeingang", None)
    if wert is None or wert is False:
        # `false`: ausdruecklich ohne Bildeingang (Entscheid 138 — Abschalten bleibt moeglich).
        return None
    unten, oben = BILDEINGANG_SPANNE
    if isinstance(wert, bool) or not isinstance(wert, (int, float)) \
            or not math.isfinite(float(wert)) or not (unten <= float(wert) <= oben):
        maengel.append(
            f"'vis.bildeingang' ist {wert!r}, erwartet war eine Staerke von {unten} bis "
            f"{oben}, false (aus) oder null (Vorgabe).")
        return None
    saetze = []
    if skip:
        saetze.append("'vis.bildeingang' und 'vis.skip' zugleich: «Nur Grundlage» rechnet "
                      "kein KI-Bild — ein Bildeingang bestellt nichts.")
    if guete == GUETE_VORSCHAU:
        saetze.append("'vis.bildeingang' und 'vis.guete: vorschau' zugleich: Die Vorschau "
                      "rechnet immer gleich (Entscheid 104); der Bildeingang ist ein Messweg "
                      "der vollen Guete.")
    if backbone_name and not _backbone.bildeingang_weg_fuer(backbone_name):
        saetze.append(f"'vis.bildeingang' an {backbone_name!r}: Fuer dieses Modell ist kein "
                      f"Weg vorbereitet, auf dem das Cycles-Bild zusaetzlich zur Tiefe ankommt.")
    maengel.extend(saetze)
    endgueltig.extend(saetze)
    return float(wert)


#: **Die Vorgabe für Varianten (Entscheid 126, 21.10.2026, Klickfrage A des Owners):** M2 —
#: der Stoff vorne, der Umriss im Lauf gehalten — und dazu der Himmel sichtbar. Fehlt ein
#: Schalter in der Bestellung (oder steht ``null``), gilt am Heim-PC dieser Wert; ein
#: ausdrücklich gesetzter Schalter gewinnt, auch «aus» (``false``). Die App schickt die drei
#: Schalter heute nicht mit (sie stehen nicht im Vertrag) — die Vorgabe gilt darum für jede
#: Bestellung aus der Knotenansicht. Wo ein Schalter fachlich nicht passt (``skip`` ohne
#: KI-Schritt, eine Skizze, keine Stimmung, das Gipsmodell), entfällt die Vorgabe
#: still mit Grund in ``messschalter`` — ein ausdrücklicher Schalter bleibt dort ein Mangel.
#:
#: **Dazu seit Entscheid 138 (22.10.2026, über die Zentrale, auf Grund von auf-20261022-337):**
#: ``bildeingang`` 0,5 — die KI-Variante geht vom Grundbild aus (337: Kanten im Haus 0,334
#: gegen 0,207 ohne, Giebelfenster gehalten, KI 13,5 s statt 16,3 s). Nur an einem Modell mit
#: vorbereitetem Weg (``Backbone.bildeingang_weg``) und **nie** an einem Modell mit offener
#: Lizenz oder Forschungslizenz (``lizenz_offen`` / ``nur_forschung``) — dort entfällt sie mit
#: Satz in den Warnungen. Ersetzt für Varianten Entscheid 117a («nur Messschalter»).
#:
#: **Seit Entscheid 149 (24.10.2026):** fuer Varianten (Auftrag auf einer Grundlage) 0,7; das erste
#: Bild ohne Grundlage behaelt 0,5 (:func:`bildeingang_vorgabe_fuer`). Ein «freies Bild»
#: (``vis.freies_bild``) setzt Bildeingang und Umriss halten aus, wo nicht ausdruecklich bestellt.
VARIANTEN_VORGABE = {"material_vorne": True, "umriss_halten": "im_lauf",
                     "himmel_sichtbar": True, "bildeingang": BILDEINGANG_VORGABE_VARIANTE}
#: Woher der Wert eines Schalters kommt (``messschalter.<name>.herkunft``).
HERKUNFT_BESTELLT = "bestellt"
HERKUNFT_VORGABE = "vorgabe"
#: Vorgabe nicht angewandt — der Grund steht daneben.
HERKUNFT_ENTFAELLT = "vorgabe_entfaellt"
#: Auf einer wiederverwendeten Grundlage: der Wert der Grundlage (nur ``himmel_sichtbar``).
HERKUNFT_GRUNDLAGE = "grundlage"
#: Die Modelle, an denen «Umriss halten im Lauf» gemessen ist (auf-20261021-303/309/314) — der
#: Weg greift in die Latenten der Z-Image-Pipeline (``render._umriss_halten_vorbereiten``). Für
#: ein anderes Modell entfällt die Vorgabe; bestellt bleibt bestellt.
UMRISS_IM_LAUF_GEMESSEN = ("z-image-turbo",)


#: Herkunft eines Schalters, den das «freie Bild» (Entscheid 149) ausgeschaltet hat.
HERKUNFT_FREIES_BILD = "freies_bild"
#: Der Anfang des Satzes am freien Bild — im Ergebnis (``qa.verdict.hinweise``) und im Befund.
SATZ_FREIES_BILD = "FREIES BILD (Entscheid 149)"


def bildeingang_vorgabe_fuer(*, variante: bool) -> float:
    """Die Vorgabe-Stärke des Bildeingangs: 0,7 für eine Variante (Entscheid 149), sonst 0,5 (138)."""
    return BILDEINGANG_VORGABE_VARIANTE if variante else BILDEINGANG_VORGABE


def bildeingang_fuer_situationsmodell(szene: dict, situation: dict | None) -> dict:
    """Die Szene mit der Vorgabe für ein Situationsmodell (Entscheid 149, ergänzt) — oder unverändert.

    Greift nur, wenn (1) die Variante den Bildeingang aus der VORGABE trägt (eine eigene Stärke
    gewinnt, ein freies Bild bleibt frei, eine entfallene Vorgabe bleibt entfallen) und (2)
    ``situation`` (aus ``kameras.ist_situationsmodell`` am Modell oder aus der Vogelschau der
    Grundlage) ``ja: True`` sagt. Dann 0,5 mit Herkunft :data:`HERKUNFT_VORGABE_SITUATION` und
    dem Grund. Ein unlesbares Modell (``ja: None``) bleibt beim Haus (0,7) — gesagt im Grund
    nicht nötig, weil nichts geändert wird.
    """
    eintrag = ((szene or {}).get("messschalter") or {}).get("bildeingang") or {}
    if not (isinstance(situation, dict) and situation.get("ja") is True):
        return szene
    if eintrag.get("herkunft") != HERKUNFT_VORGABE or szene.get("bildeingang") is None:
        return szene
    if float(szene["bildeingang"]) <= BILDEINGANG_VORGABE_SITUATION:
        return szene
    messschalter = dict(szene.get("messschalter") or {})
    messschalter["bildeingang"] = {
        "herkunft": HERKUNFT_VORGABE_SITUATION,
        "grund": (f"Situationsmodell — Vorgabe Bildeingang {BILDEINGANG_VORGABE_SITUATION:g} statt "
                  f"{BILDEINGANG_VORGABE_VARIANTE:g} (Entscheid 149, ergänzt): "
                  f"{situation.get('grund') or 'eine Anlage, kein einzelnes Haus'}")}
    return dict(szene, bildeingang=BILDEINGANG_VORGABE_SITUATION, messschalter=messschalter)


def lies_freies_bild(vis, *, skip, skizze: bool, maengel: list, endgueltig: list) -> bool:
    """``vis.freies_bild`` (Entscheid 149): ``true``, ``false`` oder null — ein bewusst freies Bild.

    Ein Stimmungsbild ohne das Grundbild als Start (txt2img mit der Tiefe) und ohne «Umriss halten»:
    Der Prompt kommt an (Licht in den Fenstern, Wiese — Messung 353, T-o), Form und Fenster halten
    nicht. Darum ist es nie Vorgabe und traegt die Kennzeichnung bis ins Ergebnis
    (``freies_bild: true``, Satz :data:`SATZ_FREIES_BILD`). Endgueltige Maengel: mit «nur
    Grundlage» (kein KI-Bild), mit einer Skizze (sie fuehrt ihr eigenes Bild) und mit einer
    ausdruecklichen Staerke ``vis.bildeingang`` (Widerspruch). Ein anderer Wert: Mangel.
    """
    wert = wert_oder(vis, "freies_bild", False)
    if not isinstance(wert, bool):
        maengel.append(f"'vis.freies_bild' ist {wert!r}, erwartet war true, false oder null.")
        return False
    if not wert:
        return False
    saetze = []
    if skip:
        saetze.append("'vis.freies_bild' und 'vis.skip' zugleich: «Nur Grundlage» rechnet kein "
                      "KI-Bild — es gibt kein freies Bild.")
    if skizze:
        saetze.append("'vis.freies_bild' mit einer Skizze: Die Skizze fuehrt ihr eigenes Bild, "
                      "sie rechnet ohnehin ohne Grundbild.")
    bi = vis.get("bildeingang") if isinstance(vis, dict) else None
    if bi is not None and bi is not False:
        saetze.append(f"'vis.freies_bild' und 'vis.bildeingang: {bi!r}' zugleich: Ein freies Bild "
                      f"rechnet ohne Grundbild als Start — eine Staerke widerspricht ihm.")
    maengel.extend(saetze)
    endgueltig.extend(saetze)
    return not saetze


def lies_variante(vis, *, maengel: list) -> bool:
    """``vis.variante`` (Mac-Probe 0.3.66, 25.10.2026): ``true``, ``false`` oder null.

    **Anlass:** Am Mac bestellte Claude ``vis_varianten`` ohne eigene Staerke; das Ergebnis trug
    Bildeingang 0,5 mit Herkunft «vorgabe» — die Staerke des ERSTEN Bilds. Bis hierhin war eine
    Variante nur an ``vis.grundlage`` zu erkennen, und der Varianten-Knoten schickt sie nur, wenn
    am Render-Knoten die Grundlage genau dieses Stands liegt (sonst rechnet Blender neu, und der
    Auftrag sah aus wie ein erstes Bild). Jetzt sagt die Bestellung es selbst (Varianten-Knoten und
    «Variante erzeugen», Vertrag ``vis.variante``). Ein anderer Wert ist ein Mangel; «nur
    Grundlage» und eine Skizze rechnen keine Staerke — dort hat das Feld keine Wirkung, ohne Mangel.
    """
    wert = wert_oder(vis, "variante", False)
    if not isinstance(wert, bool):
        maengel.append(f"'vis.variante' ist {wert!r}, erwartet war true, false oder null.")
        return False
    return wert


def widersprueche_beim_annehmen(szene) -> list[str]:
    """Die Widersprueche der Bestellung, die schon die Bruecke abweist (400) — ``[]`` sonst.

    **Ergebnis 357 (S3, Gegenprobe):** ``vis.freies_bild`` mit ``vis.bildeingang: 0.7`` wurde an
    der Bruecke angenommen, wartete auf «Freigeben» und endete erst danach beim Abholer mit Satz.
    Der Grund: ``knotenweg.lege_an`` prueft beim Annehmen nur, ob die Variante zu ihrer Grundlage
    passt; alle Maengel aus :func:`lies_szene` sieht erst der Abholer. Hier stehen die
    Widersprueche, die allein aus der Bestellung folgen (keine Datei, kein Modell, kein Rechner
    noetig) — dieselbe Pruefung wie im Lauf (:func:`lies_freies_bild`), keine zweite.
    """
    if not isinstance(szene, dict):
        return []
    vis = szene.get("vis") if isinstance(szene.get("vis"), dict) else {}
    maengel: list[str] = []
    endgueltig: list[str] = []
    lies_freies_bild(vis, skip=vis.get("skip") is True,
                     skizze=szene.get("skizze") is not None, maengel=maengel,
                     endgueltig=endgueltig)
    return endgueltig


def freies_bild_satz() -> str:
    """Der Satz am freien Bild (Entscheid 149) — ein Bild, das nie fuer modelltreu gehalten wird."""
    return (f"{SATZ_FREIES_BILD}: ohne Grundbild als Start gerechnet, nur aus Text und Tiefe — ein "
            f"Stimmungsbild, kein modelltreues Bild; das Haus kann vom Modell abweichen. Die Saetze "
            f"zu Form und Fenster bleiben stehen.")


def bestellt_schalter(vis, name: str) -> bool:
    """Steht der Schalter ausdrücklich in der Bestellung (nicht fehlend, nicht ``null``)?"""
    return isinstance(vis, dict) and vis.get(name) is not None


def varianten_vorgabe_entfaellt(name: str, *, skip, guete, skizze: bool,
                                umgebung: dict | None, backbone: str | None = None) -> str | None:
    """Warum die Vorgabe :data:`VARIANTEN_VORGABE` für diesen Schalter **nicht** gilt — oder None."""
    if skizze:
        return "eine Skizze fuehrt ihr eigenes Bild, sie ist keine Variante einer Grundlage"
    if name == "himmel_sichtbar":
        # Der Himmel ist Teil der GRUNDLAGE (Lichtdaten an Blender) — er gilt auch fuer
        # «Nur Grundlage», damit die Varianten darauf ihn tragen.
        if not (umgebung or {}).get("preset"):
            return "keine Stimmung bestellt — ohne sie gibt es kein Himmelsbild"
        from . import stimmung as _stimmung  # noqa: PLC0415
        if umgebung.get("preset") == _stimmung.PRESET_WEISS:
            return "das Gipsmodell (Stimmung «weiss») bleibt vor dem ruhigen Verlauf"
        return None
    if skip:
        return "«Nur Grundlage» rechnet kein KI-Bild"
    # DIE VORSCHAU HAELT DEN UMRISS AUCH (auf-20261022-327, B1): Bis 0.3.31 entfiel die Vorgabe
    # hier «weil die Vorschau immer gleich rechnet» — Entscheid 104 sagt aber nur, WOMIT sie
    # rechnet (z-image-turbo, ein Startwert, 8 Schritte, kleineres KI-Bild), nicht, dass sie
    # ohne Messschalter rechnet. Die Vorschau bekam so die HALBE M2: den Stoff vorne, der allein
    # weiter ueber den Umriss baut (303: M1 3,08 gegen K 2,19), ohne den Umriss-Halt, der das
    # auffaengt — in der Generalprobe 161/179 % Baumasse neben dem Haus. Die Vorschau rechnet
    # immer mit VORSCHAU_BACKBONE; gemessen ist der Halt an genau diesem Modell.
    if name == "umriss_halten" and guete == GUETE_VORSCHAU:
        backbone = _backbone.VORSCHAU_BACKBONE
    if name == "umriss_halten" and backbone not in UMRISS_IM_LAUF_GEMESSEN:
        return (f"am Bildmodell {backbone!r} ist «Umriss halten im Lauf» nicht gemessen "
                f"(gemessen: {', '.join(UMRISS_IM_LAUF_GEMESSEN)})")
    if name == "bildeingang":
        return bildeingang_vorgabe_entfaellt(guete=guete, backbone=backbone)
    return None


def bildeingang_vorgabe_entfaellt(*, guete, backbone) -> str | None:
    """Warum die Vorgabe ``bildeingang`` (0,5 nach 138, für Varianten 0,7 nach 149) an diesem Lauf
    entfällt — oder None.

    Die Auflagen des Entscheids: nur ein Modell, das den Bildeingang trägt (vorbereiteter Weg
    ``Backbone.bildeingang_weg``), und **nie** ein Modell mit offener Lizenz oder
    Forschungslizenz. Dazu die Vorschau: Sie rechnet nach Entscheid 104 immer gleich, und der
    Bildeingang ist bei ihren 8 Schritten nicht gemessen (ausdrücklich bestellt ist er dort
    ein Mangel, :func:`lies_bildeingang`).
    """
    if guete == GUETE_VORSCHAU:
        return ("die Vorschau rechnet immer gleich (Entscheid 104); der Bildeingang ist bei "
                "ihren Schritten nicht gemessen")
    if not backbone:
        return "kein Bildmodell genannt"
    try:
        eintrag = _backbone.hole(str(backbone))
    except _backbone.BackboneError:
        return f"Bildmodell {backbone!r} steht nicht im Register"
    if getattr(eintrag, "lizenz_offen", None) or getattr(eintrag, "nur_forschung", None):
        art = "offener Lizenz" if eintrag.lizenz_offen else "Forschungslizenz"
        return (f"{SATZ_BILDEINGANG_LIZENZ}: {backbone!r} ist ein Modell mit {art} — die "
                f"Vorgabe Bildeingang gilt dort nie; die Variante rechnet ohne Grundbild "
                f"als Start, nur mit der Tiefe")
    if not _backbone.bildeingang_weg_fuer(str(backbone)):
        return (f"am Bildmodell {backbone!r} ist kein Weg vorbereitet, auf dem das Grundbild "
                f"als Start ankommt")
    return None


def lies_umriss_halten(vis: dict, *, skip, guete, maengel: list,
                       endgueltig: list) -> str | None:
    """``vis.umriss_halten`` (Strang Treue, 21.10.2026): ``"nachher"``, ``"im_lauf"`` oder null.

    **Vorgabe aus.** Mit einem Wert bleibt ausserhalb des Hauses das Cycles-Bild der Grundlage
    (:mod:`aiimaging.umrisshalt`): ``nachher`` mischt nach dem KI-Schritt, ``im_lauf`` hält
    den Hintergrund in jedem Schritt des Fahrplans fest. Ein Messschalter von uns, kein Feld
    des Vertrags. Endgültiger Mangel: mit «nur Grundlage» (kein KI-Bild). Mit der Vorschau
    seit auf-20261022-327 (B1) erlaubt — sie rechnet mit z-image-turbo, an dem der Halt
    gemessen ist. Ein anderer Wert: Mangel, Rückgabe ``None``.
    """
    from . import umrisshalt as _uh  # noqa: PLC0415
    wert = wert_oder(vis, "umriss_halten", None)
    if wert is None or wert is False:
        return None
    if wert not in _uh.ARTEN:
        maengel.append(f"'vis.umriss_halten' ist {wert!r}, erwartet war "
                       f"{' oder '.join(repr(a) for a in _uh.ARTEN)} oder null.")
        return None
    saetze = []
    if skip:
        saetze.append("'vis.umriss_halten' und 'vis.skip' zugleich: «Nur Grundlage» rechnet "
                      "kein KI-Bild — es gibt keinen Umriss zu halten.")
    # Mit der Vorschau KEIN Mangel mehr (auf-20261022-327, B1): Seit die Vorgabe dort gilt,
    # waere es widersinnig, denselben Wert ausdruecklich bestellt abzuweisen.
    maengel.extend(saetze)
    endgueltig.extend(saetze)
    return wert


def lies_himmel_sichtbar(vis: dict, *, umgebung_bestellt: bool, maengel: list,
                         endgueltig: list) -> bool | None:
    """``vis.himmel_sichtbar`` (auf-20261021-309, Option Himmel): true/false/null, **Vorgabe aus**.

    Mit ``true`` sieht die Kamera in Cycles das **Himmelsbild der Stimmung** statt des ruhigen
    Verlaufs (seit auf-20261020-292 die Vorgabe, weil manche Himmelsbilder ein Bodenfoto hinter
    das Haus stellten). In 309 waren die Himmel von morgen, abend und bedeckt reine Himmel; mit
    ``umriss_halten: im_lauf`` bleibt ausserhalb des Hauses genau dieses Cycles-Bild — der
    Schalter prüft, ob der flache «Modellfoto»-Hintergrund damit verschwindet. Die Vorprobe
    stellt den Himmel wie den Verlauf eine Blendenstufe vom Haus weg. Ein Messschalter von uns,
    kein Feld des Vertrags; er geht über die Lichtdaten der Stimmung an Blender und steht damit
    im Schlüssel der Grundlage (mit und ohne Schalter sind es zwei Grundlagen).

    Endgültiger Mangel: ``true`` ohne bestellte Stimmung — dann gibt es kein Himmelsbild.
    ``None`` heisst: nicht gelesen (Mangel).
    """
    wert = wert_oder(vis, "himmel_sichtbar", False)
    if not isinstance(wert, bool):
        maengel.append(
            f"'vis.himmel_sichtbar' ist {wert!r}, erwartet war true, false oder null. Ein "
            f"anderer Wert laesst sich nicht deuten — als Text waere \"false\" wahr.")
        return None
    if wert and not umgebung_bestellt:
        satz = ("'vis.himmel_sichtbar' ohne 'render.environment': Ohne Stimmung gibt es kein "
                "Himmelsbild, das die Kamera sehen koennte.")
        maengel.append(satz)
        endgueltig.append(satz)
    return wert


#: Stoffwörter, die :func:`material_vorne_satz` im (übersetzten) Prompt erkennt, wenn kein
#: Material-Knoten bestellt ist — zusätzlich zu den Stoffen der Materialbibliothek. Längere
#: zuerst, damit «exposed concrete» nicht als «concrete» gezählt wird.
STOFFE_IM_PROMPT = ("exposed concrete", "fair-faced concrete", "board-formed concrete",
                    "concrete", "red brick", "brick", "natural stone", "stone", "timber",
                    "wood", "white plaster", "plaster", "rammed earth", "sandstone")


#: Wie oft der Hauptstoff mit ``vis.material_vorne`` HOECHSTENS im ganzen Prompt steht
#: (auf-20261021-303, B3: bei E3 stand er fuenfmal — dreimal vorne, einmal im Satz des
#: Material-Knotens hinten, einmal im Prompt des Bestellers).
MATERIAL_VORNE_HOECHSTENS = 3

#: Die Wörter, an denen eine Nennung desselben Stoffs erkannt wird — «exposed concrete» und
#: «smooth fair-faced concrete» sind beide Beton. Benachbarte Wörter zählen als eine Nennung
#: («red brick masonry» ist einmal Backstein).
STOFF_KOPFWOERTER = ("concrete", "brick", "masonry", "clinker", "stone", "sandstone",
                     "timber", "wood", "plaster", "render", "earth")


def stoff_nennungen(text: str, stoff: str) -> int:
    """Wie oft ``text`` den Stoff ``stoff`` nennt — gezählt an seinen Kopfwörtern.

    Kopfwörter sind die Wörter des Stoffs aus :data:`STOFF_KOPFWOERTER` (sonst sein letztes
    Wort); eine Folge benachbarter Kopfwörter ist eine Nennung.
    """
    woerter = re.findall(r"[a-z][a-z-]*", (stoff or "").lower())
    kopf = {w for w in woerter if w in STOFF_KOPFWOERTER} or set(woerter[-1:])
    if not kopf:
        return 0
    zahl, vorher = 0, False
    for wort in re.findall(r"[a-z][a-z-]*", (text or "").lower()):
        treffer = wort in kopf
        if treffer and not vorher:
            zahl += 1
        vorher = treffer
    return zahl


def material_vorne_satz(prompt_en: str, stoffe_bestellt=(), *,
                        rest_prompt: str | None = None,
                        hoechstens: int = None) -> tuple[str | None, tuple]:
    """``(satz, stoffe)`` für ``vis.material_vorne`` — der Stoff **vor** dem Prompt, mehrfach.

    Z-Image liest den Prompt mit einem Sprachmodell (Qwen3) statt mit CLIP; eine Gewichtung
    in Klammern wie ``(concrete:1.4)`` kennt weder dieses Modell noch die Pipeline von
    diffusers — sie stünde als Text da. Was wirkt, sind **Stellung und Wiederholung**: Der
    Satz nennt den Hauptstoff dreimal und steht vorne. Hauptstoff ist der erste bestellte
    (Material-Knoten, Fassade zuerst), sonst der erste im Prompt erkannte. Kein
    Bauteilwort (``prompts.BAUTEILWOERTER``) — der Satz bestellt Stoff, kein Bauteil.
    ``(None, ())``, wenn kein Stoff zu finden ist.

    **Höchstens dreimal im ganzen Prompt** (auf-20261021-303, B3): Nennt der übrige Prompt
    (``rest_prompt``, ohne Angabe ``prompt_en``) den Stoff schon, wird der Satz vorne um so
    viele Nennungen kürzer — mindestens eine bleibt vorne. Aus «Sichtbeton» im Standardprompt
    wird also «monolithic exposed concrete building, made entirely of exposed concrete».

    ``hoechstens`` (``vis.material_vorne_nennungen``, auf-20261023-346): eine kleinere Zahl
    als :data:`MATERIAL_VORNE_HOECHSTENS` — ohne Angabe gilt sie.
    """
    if hoechstens is None:
        hoechstens = MATERIAL_VORNE_HOECHSTENS
    stoffe = [s for s in stoffe_bestellt if s]
    if not stoffe:
        text = (prompt_en or "").lower()
        kandidaten = sorted({_materialwahl.BIBLIOTHEK[k]["prompt_en"].lower()
                             for k in _materialwahl.BIBLIOTHEK} | set(STOFFE_IM_PROMPT),
                            key=len, reverse=True)
        gefunden = []
        for k in kandidaten:
            stelle = re.search(r"(?<![\w-])" + re.escape(k) + r"(?![\w-])", text)
            if stelle and not any(k in g for _, g in gefunden):
                gefunden.append((stelle.start(), k))
        stoffe = [k for _, k in sorted(gefunden)]
    if not stoffe:
        return None, ()
    haupt = stoffe[0]
    schon = stoff_nennungen(prompt_en if rest_prompt is None else rest_prompt, haupt)
    teile = (f"monolithic {haupt} building", f"made entirely of {haupt}",
             f"uniform {haupt} on all exterior surfaces")
    return ", ".join(teile[:max(1, min(hoechstens, MATERIAL_VORNE_HOECHSTENS) - schon)]), \
        tuple(stoffe)


def lies_szene(fremd: dict, *, streng: bool = True,
               umgebung_der_grundlage=UMGEBUNG_UNBEKANNT) -> dict:
    """``kosmovis.render-scene/v1`` → unsere Felder, mit allem, was dabei auffällt.

    Returns:
        ``{geometrie, out, kameras, aufloesung, hoehe, samples, controlnet_staerke,
        prompt, prompt_original, prompt_sprache, stil_modus, stil_referenzen, backbone,
        ueberspringen, hochskalieren, sonne, innenraum, innen_bestellt,
        gelaende_erwartet, warnungen, maengel}``

        ``innenraum`` ist die Innenansicht, deren Standpunkt WIR aus den Raeumen
        rechnen; ``innen_bestellt`` sagt, ob ``interior`` bestellt und angenommen war —
        auch dann, wenn die Standpunkte als benannte Kameras mitkamen (siehe
        :func:`_lies_interior`). ``gelaende_erwartet`` ist das dreiwertige ``gelaende``
        (``None`` heisst nicht angefasst, nicht ``False``).

        ``prompt`` ist die Fassung, mit der gerendert wird — englisch, wenn der Text der
        Oberfläche deutsch war. ``prompt_original`` hält den Wortlaut fest, wie er
        ankam, und ``prompt_sprache`` den ganzen Befund samt Verfahren. Drei Felder für
        einen Text, und das ist der Punkt: Wer nur die Übersetzung protokolliert, kann
        sie nie mehr prüfen.

        ``aufloesung``, ``hoehe``, ``samples``, ``controlnet_staerke``,
        ``ueberspringen`` und ``hochskalieren`` sind ``None``, wenn das Feld der
        Bestellung nicht lesbar war — NICHT GELESEN, nicht die Vorgabe; der Grund steht
        dann unter ``maengel`` (seit 23.09.2026, siehe :func:`lies_zahl`).

        ``maengel`` hält den Lauf auf, ``warnungen`` nicht. Der Unterschied ist wichtig:
        Ein unbekanntes Backbone ist ein Mangel (wir wüssten nicht, womit wir rendern),
        eine fehlende Sonnenangabe nur eine Warnung.

    ``umgebung_der_grundlage`` (Befund 340, 22.10.2026): die gelesene Stimmung der bestellten
    Grundlage (``umgebung`` ihrer Szene, ``None`` ohne Stimmung), wenn der Aufrufer sie kennt
    (``knotenweg.grundlage_passt_nicht``, ``bruecke.lies_auftrag``). Weicht das bestellte
    Licht davon ab, wird die Grundlage verworfen (:func:`licht_der_variante`) statt später mit
    «Stimmung weicht ab» abgewiesen. Ohne Angabe bleibt es bei der Prüfung im Abholer.

    Raises:
        SzenenError: kein Wörterbuch, oder ``geometry.path`` fehlt ohne gueltige
            ``vis.grundlage`` (:data:`SATZ_OHNE_PFAD`). Ohne Geometrie und ohne Grundlage gibt
            es nichts zu rendern; alles andere hat im fremden Vertrag Vorgabewerte. Mit
            Grundlage ist ``geometrie`` dann ``None``.
    """
    if not isinstance(fremd, dict):
        raise SzenenError(f"render-scene ist kein Wörterbuch: {type(fremd).__name__}")

    warnungen: list[str] = []
    # Was JEDEN Auftrag gleich trifft — siehe `vertragsvorgaben` im Rueckgabewert.
    vorgaben: list[str] = []
    maengel: list[str] = []

    # UNBEKANNTE FELDER SIND EIN MANGEL, und `maengel` haelt den Lauf auf.
    #
    # Das ist eine Entscheidung und keine Selbstverstaendlichkeit: Sie kann eine
    # bestehende Bestellung abweisen, die heute durchginge. Sie faellt so, weil der
    # andere Fall teurer ist — ein Lauf, der 775 Sekunden rechnet (gemessen auf der
    # HomeStation am 10.09.2026) und danach nicht das bestellte Bild ist, kostet mehr als
    # eine Fehlermeldung. Und er faellt NICHT auf: Wer ein Feld setzt und kein Wort hoert,
    # haelt es fuer bedient.
    #
    # `streng=False` gibt es fuer den Fall, dass der fremde Vertrag ein Feld traegt, das
    # wir noch nicht kennen, und der Betrieb nicht warten kann. Dann steht es unter
    # `warnungen` statt unter `maengel` — sichtbar bleibt es in beiden Faellen.
    unbekannt = unbekannte_felder(fremd)
    if unbekannt:
        satz = (
            f"Unbekannte Felder in der Bestellung: {', '.join(unbekannt)}. Wir wissen "
            f"nicht, was sie verlangen, und wuerden sie stillschweigend uebergehen — das "
            f"Bild waere dann nicht das bestellte, ohne dass es jemandem auffiele. "
            f"Entweder der Vertrag hat sich geaendert (dann sagt es uns), oder es ist ein "
            f"Tippfehler."
        )
        (maengel if streng else warnungen).append(satz)
    # BEKANNT UND ABGEWIESEN — dieselbe Wirkung wie ein unbekanntes Feld, aber mit dem
    # Grund je Feld (Antwort auf auf-20260911-104, uebertragen am 22.09.2026). `streng`
    # gilt hier genauso: Der Ausweg soll fuer diese Felder nicht enger werden, als er fuer
    # sie war, solange sie noch «unbekannt» hiessen.
    for satz in abgewiesene_felder(fremd):
        (maengel if streng else warnungen).append(satz)

    kennung = fremd.get("schema", SCHEMA_SZENE)
    if kennung != SCHEMA_SZENE:
        warnungen.append(
            f"Fremde Schemakennung {kennung!r} statt {SCHEMA_SZENE!r}. Gelesen wird "
            f"trotzdem — aber wenn sich der Vertrag geändert hat, stimmt hier "
            f"möglicherweise ein Feldname nicht mehr, und das fällt nicht auf."
        )

    geo = fremd.get("geometry") or {}
    # KEIN BLOCK, KEIN PFAD — Durchsicht 23.09.2026: Ein `geometry`, das kein Block ist,
    # stuerzte hier mit AttributeError ab und nahm ueber `bruecke.lies_auftrag` den ganzen
    # Durchgang des Abholers mit. Ohne Block gibt es keinen Pfad, also dieselbe Antwort
    # wie ohne Pfad.
    if not isinstance(geo, dict):
        raise SzenenError(
            f"render-scene mit 'geometry' vom Typ {type(geo).__name__} statt eines "
            f"Blocks — es gibt keinen 'geometry.path' und nichts zu rendern.")
    pfad = geo.get("path")
    # OHNE PFAD NUR ALS VARIANTE EINER GRUNDLAGE (Fehler Test-App R48, 21.10.2026). Ihr Vertrag
    # (render-scene.ts, `vis.grundlage`, Fehler-Nachgang 20.10.2026) laesst die Anlage mit
    # `vis.grundlage` OHNE Modelldatei zu, `geometry.path` bleibt dann leer. Bis dahin warf
    # diese Stelle immer, und der Abholer liess «Variante erzeugen» mit diesem Satz liegen —
    # die Variante rechnete nie. Seither: Traegt die Bestellung eine gueltige Kennung, ist der
    # leere Pfad kein Fehler; die Kameras und Passes kommen aus der abgelegten Grundlage
    # (`abholer.lies_grundlage`), das Modell — wenn noch da — aus dem Auftrag, der sie
    # gerechnet hat (`bruecke.lies_auftrag`). Ohne gueltige Kennung bleibt der Satz.
    if not pfad:
        if not hat_gueltige_grundlage(fremd):
            raise SzenenError(SATZ_OHNE_PFAD)
        pfad = None
    # EIN FORMAT, DAS KEIN TEXT IST, IST EIN MANGEL — und kein Absturz (Durchsicht
    # 23.09.2026, nachgestellt mit `format: 5`: AttributeError aus `.lower()`, ueber die
    # Bruecke bis in `abholer.hole_einen`). Es wird auch nicht geraten: Das Format
    # waehlt in `bruecke.lies_auftrag` die Datei (model.ifc oder model.glb).
    roh_fmt = geo.get("format")
    if roh_fmt is not None and not isinstance(roh_fmt, str):
        maengel.append(
            f"'geometry.format' ist {roh_fmt!r} und kein Text. Euer Vertrag fuehrt es als "
            f"Wort ({', '.join(FREMDE_FORMATE)}); welches gemeint ist, raten wir nicht — "
            f"das Format entscheidet, welche Datei gerechnet wird.")
        roh_fmt = None
    fmt = (roh_fmt or "").lower()
    if fmt and fmt not in FREMDE_FORMATE:
        warnungen.append(f"Format {fmt!r} steht nicht im fremden Vertrag ({', '.join(FREMDE_FORMATE)}).")
    if fmt and fmt not in UNSERE_FORMATE:
        maengel.append(
            f"Format {fmt!r} verarbeiten wir nicht. Unsere Kette kann "
            f"{', '.join(UNSERE_FORMATE)} — 'fbx' und 'blend' bräuchten einen "
            f"Konverter, den es nicht gibt. Abgelehnt, statt zwei Stufen später "
            f"unverständlich zu scheitern."
        )

    # EIN BLOCK, DER KEINER IST, IST EIN MANGEL — und kein Absturz (Durchsicht der
    # Runde 7, 23.09.2026, nachgestellt mit `render: "x"`: AttributeError aus `.get`,
    # ueber die Bruecke bis in `abholer.durchgang`). Gelesen wird dann, als fehlte der
    # Block; der Mangel haelt den Lauf auf, bevor eine Vorgabe ein Bild ergibt.
    render = _block(fremd, "render", maengel)
    # Ob die Bildmasse GEWAEHLT oder geerbt sind, entscheidet, wo der Rundungshinweis
    # landet: Die Vorgabe des fremden Vertrags ist 1600x1000 und damit nie ein Vielfaches
    # von 16 — dieser Hinweis trifft jeden Auftrag gleich. Wer selbst 999x777 bestellt,
    # bekommt ihn dagegen als Warnung ueber SEINE Bestellung.
    gewaehlt = render.get("resolution") is not None
    aufl = render.get("resolution") or [1600, 1000]
    if not (isinstance(aufl, (list, tuple)) and len(aufl) == 2):
        warnungen.append(f"'render.resolution' ist kein Paar: {aufl!r} — es gilt 1600x1000.")
        aufl = [1600, 1000]
        gewaehlt = False
    # JEDE ZAHL DER BESTELLUNG GEHT DURCH `lies_zahl` (Befund 23.09.2026, dort): Eine
    # unlesbare ist ein Mangel mit Satz, und ihr Feld bleibt `None` — NICHT GELESEN, nicht
    # die Vorgabe. Der Mangel haelt den Lauf auf, bevor jemand das Feld liest.
    # Die Regeln sind DIESELBEN wie am MCP-Einlass (`REGEL_KANTE`, `REGEL_SAMPLES`, Runde
    # 7c): Was der Einlass abweist, haelt hier auf, und umgekehrt.
    masse = [lies_zahl(w, f"render.resolution[{k}]", **REGEL_KANTE)
             for k, w in enumerate(aufl)]
    maengel.extend(satz for _, satz in masse if satz)
    if all(satz is None for _, satz in masse):
        # BLENDER RECHNET DIE BESTELLTE GROESSE (Befund B5 aus auf-20261020-292): Bis dahin
        # wurde hier auf das Raster abgerundet, und Blender rechnete 960x592 statt 960x600 —
        # Seitenverhaeltnis 1,6216 statt 1,6, und der Knoten «Kamera» (der mit 1,6 rechnet)
        # stand 1,06 m neben dem Heim-PC. Nur der KI-Schritt braucht das Raster; er rechnet
        # intern darauf und bringt sein Bild zurueck (`abholer.ki_steuerbilder`).
        aufl = [int(zahl) for zahl, _ in masse]
        hinweis = _ki_raster_hinweis(aufl)
        if hinweis:
            (warnungen if gewaehlt else vorgaben).append(hinweis)
    else:
        aufl = [None, None]

    samples, satz = lies_zahl(wert_oder(render, "samples", 128), "render.samples",
                              **REGEL_SAMPLES)
    if satz:
        maengel.append(satz)
    # Mit Wertebereich seit der Runde 8 (23.09.2026, siehe `REGEL_TREUE`): `5.0` ist
    # ein Mangel, und das Feld bleibt `None` — dann steht auch kein Abbildungssatz da.
    treue, satz = lies_zahl(wert_oder(render, "faithful", 0.8), "render.faithful",
                            **REGEL_TREUE)
    if satz:
        maengel.append(satz)
    if treue is not None:
        # KEIN SATZ UEBER EINE ABBILDUNG, DIE NICHT STATTFAND (Durchsicht der Runde 7b,
        # 23.09.2026). Bei unlesbarem 'faithful' stand hier «'faithful' (None) wird auf
        # 'controlnet_staerke' abgebildet» — abgebildet wurde nichts, der Grund steht
        # unter `maengel`, und nur dort.
        vorgaben.append(
            f"'faithful' ({treue}) wird auf 'controlnet_staerke' abgebildet — die einzige "
            f"ehrliche Zuordnung. Was dabei NICHT abgebildet wird: 'denoise' und die "
            f"Schrittzahl beeinflussen die Treue mit, und die Wirkung ist nicht monoton "
            f"(auf-20260818-13: 0.80 schneidet besser ab als 1.00). Ein einzelner Regler "
            f"von 0 bis 1 kann das nicht ausdrücken."
        )

    stil = _block(fremd, "style", maengel)
    vis = _block(fremd, "vis", maengel)
    # OHNE ANGABE DAS VORGABEMODELL IHRES VERTRAGS (29.09.2026, Antwort auf-155 F6):
    # `vis.backbone` hat drüben die Vorgabe 'z-image-turbo' (render-scene.ts). Hier stand
    # 'qwen' — das Bearbeitungsmodell, das die Tiefe nicht als Steuerung nimmt, 349 s statt
    # 47 s je Bild braucht und auf dem Testbau ein erfundenes Haus statt des Quaders
    # zeichnete (auf-169, Kamera s). Ihre App schickt das Feld immer; betroffen waren
    # Bestellungen ohne Angabe, etwa über den MCP-Einlass. `wert_oder`: null = fehlt.
    fremd_bb = wert_oder(vis, "backbone", "z-image-turbo")
    if not isinstance(fremd_bb, str):
        # Eine Liste als Kuerzel warf TypeError aus dem Nachschlagen (23.09.2026).
        bb = {"name": None, "bekannt": False, "zulaessig": False, "begruendung": (
            f"'vis.backbone' ist {fremd_bb!r} und kein Kuerzel. Welches Modell gemeint "
            f"ist, raten wir nicht — ein ersetztes Modell waere ein anderes Bild unter "
            f"demselben Auftrag.")}
    else:
        bb = backbone_von_fremd(fremd_bb)
    if not bb["bekannt"]:
        maengel.append(bb["begruendung"])
    elif not bb["zulaessig"]:
        maengel.append(f"Backbone {bb['name']!r} ist unter Regel 1 ausgeschlossen: {bb['begruendung']}")

    kameras = fremd.get("cameras", "auto")
    if isinstance(kameras, list):
        kameras = [spec_zu_kamera(s) for s in kameras]
    elif kameras == "saved":
        maengel.append(
            "cameras='saved' verlangt gespeicherte Kameras aus der fremden Szene. Wir "
            "haben keinen Zugriff darauf und würden sonst stillschweigend 'auto' "
            "rendern — also andere Blickwinkel als bestellt."
        )

    innenraum, innen_bestellt = _lies_interior(
        fremd.get("interior"), kameras=kameras, fmt=fmt,
        warnungen=warnungen, maengel=maengel)

    # DAS GELAENDE, DREIWERTIG — die Antwort auf unseren eigenen Auftrag auf-20260901-67.
    # Drueben gebaut als `gelaende: boolean | null`, Vorgabe null («unbekannt», nie still
    # false). Bis zum 22.09.2026 kannte unsere Karte das Feld nicht und haette eine
    # Bestellung, die es setzt, abgewiesen — obwohl WIR es bestellt hatten. `None` heisst
    # hier NICHT ANGEFASST: Dann gilt, was der Abholer prozessweit eingestellt hat.
    gelaende = fremd.get("gelaende")
    if gelaende is not None and not isinstance(gelaende, bool):
        maengel.append(
            f"'gelaende' ist {gelaende!r}. Euer Vertrag fuehrt es dreiwertig (true, false "
            f"oder null, auf-67); ein anderer Wert laesst sich nicht deuten, und ein "
            f"geratener Gelaendebefund macht die Bauwerksmaske falsch.")
        gelaende = None

    ebenen = _lies_passes(render.get("passes"), maengel)

    # DIE UMGEBUNG (Entscheid 76, 08.10.2026) — siehe `kontext_aus_szene`. Ihre Maengel
    # halten den Lauf an wie jeder andere.
    kontext_block = kontext_aus_szene(fremd.get("context"))
    kontext_weggelassen = None
    if kontext_block is not None and kontext_block.get("weggelassen"):
        # EINE PUNKTWOLKE OHNE SPLAT-FELDER (R59): weggelassen, mit Satz — und ohne ihre
        # Maengel (Lage, fit): Was nicht gerechnet wird, haelt den Lauf nicht an.
        kontext_weggelassen = {"datei": kontext_block.get("datei"),
                               "fehlende_felder": list(kontext_block.get("fehlende_felder")
                                                       or ()),
                               "satz": kontext_block["weggelassen"]}
        warnungen.append(kontext_block["weggelassen"])
        kontext_block = None
    if kontext_block is not None:
        maengel.extend(kontext_block["maengel"])

    # DIE SKIZZE (Entscheid 96, 15.10.2026) — siehe `skizze_aus_szene`. Was mit ihr nicht
    # zusammengeht, steht unten bei den Schaltern (dort ist `skip` gelesen).
    skizze_block = skizze_aus_szene(fremd.get("skizze"))
    if skizze_block is not None:
        maengel.extend(skizze_block["maengel"])

    sonne = render.get("sun")
    if sonne is not None and not isinstance(sonne, dict):
        maengel.append(f"'render.sun' ist {sonne!r} und kein Block {{azimuth, elevation}}.")
        sonne = None
    elif sonne is not None:
        # IHRE KONVENTION, NICHT UNSERE VORGABE (24.09.2026, bei der Nachmessung zu B161).
        # Hier stand eine Warnung, der Azimut gelte unter der ANNAHME 'von Süden', und ob
        # ihr Vertrag von Norden zähle, sei «nicht geklärt». Ihr Vertrag sagt es seit
        # langem wörtlich: im Uhrzeigersinn ab Nord (sonne.KOSMO_KONVENTION). Jede
        # bestellte Sonne stand damit um 180 Grad verdreht.
        sonne = dict(sonne, konvention=_sonne.KOSMO_KONVENTION)
        try:
            befund = _sonne.aus_bestellung(sonne)
        except _sonne.SonnenError as fehler:
            maengel.append(f"'render.sun' ist nicht zu bedienen: {fehler}")
            befund = None
        if befund is not None:
            satz = (f"Sonnenstand bedient: Höhe {befund['hoehe_grad']:g} Grad, Azimut "
                    f"{befund['azimut_grad']:g} Grad im Uhrzeigersinn ab Nord (euer "
                    f"Vertrag, render-scene.ts).")
            if befund["licht_bestellt"]:
                satz += (f" Dazu {', '.join(befund['licht_bestellt'])} an der Sonne des "
                         f"Cycles-Schritts. Vorbehalt: Das gelieferte KI-Bild entsteht aus "
                         f"der Tiefenkarte; beim Vorgabemodell kommt das Cycles-Bild — und "
                         f"mit ihm dieses Licht — darin nicht an (gemessen, auf-123, "
                         f"auf-137 V5).")
            warnungen.append(satz)
    if sonne is None:
        vorgaben.append(
            "Keine Sonnenangabe. Unser Runner setzt eine feste Sonne von schräg "
            "vorn-oben; der Sonnenstand des Auftrags wird damit NICHT bedient."
        )

    # Der Prompt der Oberfläche ist deutsch — gemessen, nicht vermutet.
    #
    # Die Vis sammelt deutschen Text und legt ihn wörtlich in `style.prompt`. Am Gerät
    # (HomeStation `9a33353`) über 8 gepaarte Startwerte: der deutsche Prompt ergab
    # 8 von 8 Mal einen deutlich blaueren Himmel als der gleichbedeutende englische.
    # Deshalb wird hier übersetzt — und zwar an DIESER Stelle, weil es die Naht ist, an
    # der fremder Text in unsere Rechnung eintritt. Weiter innen wüsste niemand mehr,
    # dass der Text je deutsch war.
    #
    # Deklariert, nicht heimlich (Owner-Entscheid 2026-08-21): `prompt_original` behält
    # den Wortlaut der Oberfläche, und eine Warnung sagt, dass übersetzt wurde.
    roh_prompt = stil.get("prompt", "")
    sprachbefund = sprache.uebersetze(roh_prompt)
    if sprachbefund["noetig"]:
        warnungen.append(
            f"Der Prompt der Oberfläche war deutsch und wurde übersetzt "
            f"({sprachbefund['verfahren']}): {sprachbefund['original']!r} → "
            f"{sprachbefund['uebersetzt']!r}. Gerendert wird die englische Fassung. "
            f"Grund: Die Bildmodelle sind an englischen Bild-Text-Paaren trainiert; "
            f"am Gerät ergab 'bedeckter Himmel' bei 8 von 8 gepaarten Startwerten einen "
            f"deutlich blaueren Himmel als 'overcast sky'."
        )
        warnungen.extend(sprachbefund["warnungen"])

    # DER BAUTEILWÄCHTER — die direkte Antwort auf den teuersten Fehler dieses Projekts,
    # und bis zum 23.08.2026 lief er auf keinem einzigen echten Auftrag.
    #
    # Er entstand aus `auf-20260818-09`: „clean flat roof" für einen oben offenen Quader,
    # und das Bildmodell lieferte ein Dach. Es hat nichts falsch gemacht — es tat, was
    # dastand. Seither steht in `prompts.py` ein Wächter dagegen, geprüft und begründet,
    # **von nichts aufgerufen**: `komponiere` ruft ihn, aber `komponiere` liegt nicht auf
    # dem Weg, den ein Auftrag der Oberfläche nimmt. Der bringt seinen Prompt roh mit.
    #
    # Geprüft werden BEIDE Fassungen. Das Original, weil der Wächter deutsche
    # Bauteilwörter kennt; die Übersetzung, weil ein deutsches „Dach" erst als ``roof``
    # sicher gefunden wird — und weil sonst genau die Wörter durchrutschten, die die
    # Übersetzung selbst erzeugt hat.
    bauteile: list[str] = []
    for fassung in (sprachbefund["original"], sprachbefund["uebersetzt"]):
        for wort in prompts.bauteilwaechter(fassung)["woerter"]:
            if wort not in bauteile:
                bauteile.append(wort)
    if bauteile:
        warnungen.append(prompts.bauteilwaechter(" ".join(bauteile))["hinweis"])

    # WAHRHEITSWERTE WERDEN GELESEN, NICHT UMGEWANDELT (23.09.2026): `bool("false")` ist
    # True — `skip: "false"` haette den Lauf still abbestellt. Dieselbe Regel wie bei
    # `gelaende`: Was nicht true, false oder null ist, ist ein Mangel, und das Feld
    # bleibt `None` (nicht gelesen).
    schalter = {}
    for name in ("skip", "upscale"):
        wert = wert_oder(vis, name, False)
        if isinstance(wert, bool):
            schalter[name] = wert
        else:
            schalter[name] = None
            maengel.append(
                f"'vis.{name}' ist {wert!r}, erwartet war true, false oder null. Ein "
                f"anderer Wert laesst sich nicht deuten — als Text waere \"false\" wahr.")
    endgueltig: list[str] = []
    grundlage, seed = _lies_grundlage_und_seed(vis, schalter.get("skip"),
                                               skizze_block is not None, maengel, endgueltig)
    guete = _lies_guete(vis, schalter.get("skip"), maengel, endgueltig)
    # DAS UMFELD (Knoten «Umfeld», 24.10.2026) — siehe `umfeld.lies_wunsch`. Ein falsch
    # geschriebener Wunsch haelt auf wie jedes unbekannte Feld. Mit Skizze rechnet kein Blender —
    # dann wirkt es nicht, und das steht als Warnung da.
    umfeld_wunsch, umfeld_maengel = _umfeld.lies_wunsch(
        vis.get("umfeld") if isinstance(vis, dict) else None)
    maengel.extend(umfeld_maengel)
    if umfeld_wunsch is not None and skizze_block is not None:
        warnungen.append("Umfeld bestellt, aber eine Skizze fuehrt das Bild: Sie rechnet keine "
                         "Blender-Grundlage, in die Baeume und Autos gestellt wuerden — das "
                         "Umfeld wirkt hier nicht.")
        umfeld_wunsch = None
    # DIE STIMMUNG (Entscheide 107/110/113, 20.10.2026) — siehe `umgebung_aus_szene`. Fehlt
    # das Himmelsbild am Rechner, endet der Auftrag mit Satz (endgueltig), und der Satz steht
    # im Ergebnis unter `lieferstatus_grund` (`fehlende_dateien`).
    fehlende_dateien: list[str] = []
    prompt_zusaetze: list[dict] = []
    # Der Prompt, an den die Saetze der Knoten kommen — ohne die Saetze der Stimmungen, wenn
    # eine bestellt ist (auf-20261021-306, B2; `stimmung.ohne_stimmungssaetze`).
    prompt_basis = sprachbefund["uebersetzt"]
    # DIE STIMMUNG DER VARIANTE (N6, Mac-Demolauf 22.10.2026) — siehe `stimmung_der_variante`.
    # VOR dem Lesen des Lichts und der Materialien: Ohne Grundlage laden beide ihre Dateien
    # fuer Blender. Die verworfene Kennung bleibt fuer das Modell (`bruecke`).
    environment_roh = render.get("environment")
    grundlage_bestellt = grundlage
    variante_stimmung = None
    if not schalter.get("skip") and skizze_block is None:
        variante_stimmung = stimmung_der_variante(
            prompt_basis, environment_roh, grundlage,
            prompt_original=sprachbefund.get("original"),
            # Ergebnis 342 (f): die Stimmung der Grundlage, wenn sie bekannt ist.
            licht_der_grundlage=(umgebung_der_grundlage.get("preset")
                                 if isinstance(umgebung_der_grundlage, dict) else None))
    if variante_stimmung is not None:
        environment_roh = umgebung_der_variante(environment_roh, variante_stimmung)
        grundlage = None
        warnungen.append(variante_stimmung["satz"])
    elif (grundlage is not None and not schalter.get("skip") and skizze_block is None
          and umgebung_der_grundlage is not UMGEBUNG_UNBEKANNT):
        # DAS LICHT DER VARIANTE (Befund 340) — siehe `licht_der_variante`. Das bestellte Licht
        # bleibt, wie es ist; nur die Grundlage, die ein anderes traegt, wird verworfen.
        variante_stimmung = licht_der_variante(environment_roh, umgebung_der_grundlage,
                                               grundlage)
        if variante_stimmung is not None:
            grundlage = None
            warnungen.append(variante_stimmung["satz"])
    # DER STOFF DER VARIANTE (Befund 337, 22.10.2026) — siehe `material_der_variante`. Wie N6
    # VOR dem Lesen von Licht und Materialien: Ohne Grundlage laden beide ihre Dateien.
    materialien_roh = render.get("materialien")
    material_wunsch = None
    if not schalter.get("skip") and skizze_block is None:
        material_wunsch = material_der_variante(prompt_basis, materialien_roh,
                                                grundlage_bestellt, environment=environment_roh)
    if material_wunsch is not None:
        if material_wunsch["ersetzung"] == ERSETZUNG_MATERIALWAHL:
            materialien_roh = dict(materialien_roh or {})
            materialien_roh["fassade"] = {"id": material_wunsch["id"]}
            grundlage = None
        if material_wunsch["satz"]:
            warnungen.append(material_wunsch["satz"])
    umgebung_block = umgebung_aus_szene(environment_roh, guete=guete,
                                        grundlage=grundlage)
    if umgebung_block is not None:
        maengel.extend(umgebung_block["maengel"])
        endgueltig.extend(umgebung_block["endgueltig"])
        if umgebung_block["fehlt"]:
            fehlende_dateien.append(umgebung_block["fehlt"])
        if umgebung_block["umgebung"] is not None:
            # DER SATZ DES HEIM-PC GILT, IMMER UND EINMAL (auf-20261021-306, B2): Bis dahin
            # entschied ein `merkmal` im Prompt, ob er fehlte — kam der Satz des Knotens halb
            # uebersetzt an («evening mood, warm light, leuchtende window»), fehlte er, und
            # «abend» zeigte einen Innenraum. Jetzt werden die Saetze der Stimmungen aus dem
            # Prompt genommen und der der bestellten angefuegt.
            preset = umgebung_block["umgebung"]["preset"]
            prompt_basis, herausgenommen = _stimmung.ohne_stimmungssaetze(prompt_basis)
            # KEIN TEIL DES SATZES ZWEIMAL (Ergebnis auf-20261022-342, g): «Abendstimmung» wird
            # im Glossar zu «evening mood», und der Satz des Heim-PC beginnt mit «evening mood»
            # — im Prompt stand es doppelt. Ein Teil des Prompts, der woertlich ein Teil des
            # angefuegten Satzes ist, wird herausgenommen; alles andere bleibt Wort fuer Wort.
            prompt_basis, doppelt = _stimmung.ohne_teile_des_satzes(
                prompt_basis, _stimmung.STIMMUNGEN[preset]["prompt_en"])
            zusatz = {"art": "stimmung", "preset": preset,
                      "satz": _stimmung.STIMMUNGEN[preset]["prompt_en"],
                      "schon_im_prompt": False,
                      "herausgenommen": list(herausgenommen)}
            if doppelt:
                zusatz["doppelt_herausgenommen"] = list(doppelt)
            prompt_zusaetze.append(zusatz)
    # DAS GEBAEUDEWORT (auf-20261021-309, B3): Ist der Bauteil des Prompts leer (nur der
    # Stimmungssatz war da), kommt «architectural building» VOR alle Saetze der Knoten — sonst
    # malte das Bildmodell eine Hoehle. Ein Eintrag in `prompt_zusaetze`, damit es im Ergebnis
    # steht; der Stimmungssatz bleibt einmal.
    gebaeude = zusatz_gebaeudewort(prompt_basis)
    if gebaeude:
        prompt_basis = ""
        prompt_zusaetze.insert(0, {"art": "gebaeudewort", "satz": gebaeude,
                                   "schon_im_prompt": False,
                                   "grund": "Bauteil des Prompts leer (auf-20261021-309, B3)"})
    # DIE MATERIALIEN (Entscheide 107/111/113) — siehe `materialien_aus_szene`. «weiss»
    # macht alle Oberflaechen zum Gipsmodell; Materialien daneben widersprechen sich.
    material_block = materialien_aus_szene(materialien_roh, guete=guete,
                                           grundlage=grundlage)
    if material_block is not None:
        maengel.extend(material_block["maengel"])
        endgueltig.extend(material_block["endgueltig"])
        fehlende_dateien.extend(material_block["fehlt"])
        if ((umgebung_block or {}).get("umgebung") or {}).get("preset") == \
                _stimmung.PRESET_WEISS and material_block["materialien"]:
            satz = ("Stimmung 'weiss' und 'render.materialien' zugleich: «weiss» macht alle "
                    "Oberflaechen zum Gipsmodell (Entscheid 113) — die gewaehlten Materialien "
                    "kaemen nicht ins Bild.")
            maengel.append(satz)
            endgueltig.append(satz)
        for art, wahl in (material_block["materialien"] or {}).items():
            satz, schon = _materialwahl.prompt_satz(art, wahl["id"], prompt_basis)
            prompt_zusaetze.append({"art": "material", "bauteil_art": art, "id": wahl["id"],
                                    "satz": satz, "schon_im_prompt": schon})
    # NUR DER PROMPT (Befund 337): Fuer Glas oder Metall gibt es kein Material der Bibliothek —
    # der Satz der gewaehlten Fassade faellt weg, der Wunsch steht vorne (`material_vorne`).
    wunsch_nur_prompt = (material_wunsch or {}).get("ersetzung") == ERSETZUNG_NUR_PROMPT
    if wunsch_nur_prompt:
        for z in prompt_zusaetze:
            if z.get("art") == "material" and z.get("bauteil_art") == "fassade":
                z["weggelassen"] = "material_der_variante"
    # DER ZUSATZ «LEERER HINTERGRUND» (auf-20261021-296, N3) — unser Messschalter, Vorgabe
    # aus. Gelesen wie `skip`: nur true, false oder null; mit «nur Grundlage» bestellt er
    # nichts und widerspricht der Bestellung (wie `vis.guete`).
    leer_wert = wert_oder(vis, "leerer_hintergrund", False)
    if not isinstance(leer_wert, bool):
        maengel.append(
            f"'vis.leerer_hintergrund' ist {leer_wert!r}, erwartet war true, false oder "
            f"null. Ein anderer Wert laesst sich nicht deuten — als Text waere \"false\" wahr.")
    elif leer_wert and schalter.get("skip"):
        satz = ("'vis.leerer_hintergrund' und 'vis.skip' zugleich: «Nur Grundlage» rechnet "
                "kein KI-Bild — ein Zusatz fuer den KI-Schritt bestellt nichts.")
        maengel.append(satz)
        endgueltig.append(satz)
    elif leer_wert:
        satz, schon = zusatz_leerer_hintergrund(prompt_basis)
        prompt_zusaetze.append({"art": "leerer_hintergrund", "satz": satz,
                                "schon_im_prompt": schon})
    # DIE MESSSCHALTER AUS ENTSCHEID 117 (21.10.2026) — beide Vorgabe aus, keiner im Vertrag.
    farbabgleich = lies_farbabgleich(vis, skip=schalter.get("skip"), maengel=maengel,
                                     endgueltig=endgueltig)
    # DIE MESSSCHALTER AUS DEM STRANG TREUE (21.10.2026) — beide Vorgabe aus, keiner im
    # Vertrag. `material_vorne` stellt den Stoff vor den Prompt (Satz in `prompt_zusaetze`
    # mit `vorne`); ohne Schalter ist der Prompt Wort fuer Wort derselbe.
    # DIE VORGABE FUER VARIANTEN (Entscheid 126, 21.10.2026): fehlt ein Schalter, gilt M2 mit
    # Himmel; ein ausdruecklich gesetzter gewinnt. Die Vorgabe wird VOR dem Lesen eingesetzt,
    # damit sie durch dieselbe Pruefung geht wie ein bestellter Schalter — nur dort, wo sie
    # fachlich passt (sonst entfaellt sie mit Grund, ohne Mangel).
    messschalter: dict = {}
    vis_mit_vorgabe = dict(vis) if isinstance(vis, dict) else {}
    # DAS FREIE BILD (Entscheid 149, 24.10.2026): bewusst ohne Grundbild und ohne Umriss halten —
    # wo nicht ausdruecklich anders bestellt. Gekennzeichnet bis ins Ergebnis.
    freies_bild = lies_freies_bild(vis, skip=schalter.get("skip"),
                                   skizze=skizze_block is not None, maengel=maengel,
                                   endgueltig=endgueltig)
    # DIE STAERKE JE ART (Entscheid 149): eine Variante (Auftrag auf einer Grundlage, auch eine
    # verworfene) rechnet mit 0,7, das erste Bild ohne Grundlage mit 0,5 (Entscheid 138). Seit der
    # Mac-Probe 0.3.66 auch ein Auftrag mit `vis.variante: true` ohne Grundlage (`lies_variante`).
    variante_bestellt = lies_variante(vis, maengel=maengel)
    ist_variante = grundlage_bestellt is not None or variante_bestellt
    for name, vorgabe in VARIANTEN_VORGABE.items():
        if bestellt_schalter(vis, name):
            messschalter[name] = {"herkunft": HERKUNFT_BESTELLT}
            continue
        if freies_bild and name in ("bildeingang", "umriss_halten"):
            vis_mit_vorgabe[name] = False
            messschalter[name] = {"herkunft": HERKUNFT_FREIES_BILD}
            continue
        if name == "bildeingang":
            vorgabe = bildeingang_vorgabe_fuer(variante=ist_variante)
        grund = varianten_vorgabe_entfaellt(
            name, skip=schalter.get("skip"), guete=guete, skizze=skizze_block is not None,
            umgebung=(umgebung_block or {}).get("umgebung"), backbone=bb.get("name"))
        if grund is None:
            vis_mit_vorgabe[name] = vorgabe
            messschalter[name] = {"herkunft": HERKUNFT_VORGABE}
        else:
            messschalter[name] = {"herkunft": HERKUNFT_ENTFAELLT, "grund": grund}
    umriss_halten = lies_umriss_halten(vis_mit_vorgabe, skip=schalter.get("skip"), guete=guete,
                                       maengel=maengel, endgueltig=endgueltig)
    # DER BILDEINGANG (Entscheid 138, 22.10.2026): seit dem Entscheid Vorgabe 0,5 fuer
    # Varianten — gelesen NACH der Vorgabe, damit sie durch dieselbe Pruefung geht wie ein
    # bestellter Wert. Entfaellt sie wegen der Lizenz des Modells, sagt es ein Satz.
    bildeingang = lies_bildeingang(vis_mit_vorgabe, skip=schalter.get("skip"), guete=guete,
                                   backbone_name=bb.get("name"), maengel=maengel,
                                   endgueltig=endgueltig)
    bi_grund = (messschalter.get("bildeingang") or {}).get("grund") or ""
    if bi_grund.startswith(SATZ_BILDEINGANG_LIZENZ):
        warnungen.append(f"{bi_grund}.")
    # Frei ist auch ein ausdruecklich abgeschalteter Bildeingang (`vis.bildeingang: false`, die
    # Messreihe T in 353): ohne Grundbild als Start ist kein Bild modelltreu.
    if freies_bild or (isinstance(vis, dict) and vis.get("bildeingang") is False):
        freies_bild = not schalter.get("skip") and skizze_block is None
    if freies_bild:
        warnungen.append(freies_bild_satz())
    # DER HIMMEL HINTER DEM HAUS (auf-20261021-309, Option Himmel) — seit Entscheid 126 Vorgabe.
    himmel_sichtbar = lies_himmel_sichtbar(
        vis_mit_vorgabe, umgebung_bestellt=bool(umgebung_block and umgebung_block.get("umgebung")),
        maengel=maengel, endgueltig=endgueltig)
    nennungen = lies_material_vorne_nennungen(vis_mit_vorgabe, maengel=maengel)
    vorne_wert = wert_oder(vis_mit_vorgabe, "material_vorne", False)
    if not isinstance(vorne_wert, bool):
        maengel.append(
            f"'vis.material_vorne' ist {vorne_wert!r}, erwartet war true, false oder null.")
    elif vorne_wert and schalter.get("skip"):
        satz = ("'vis.material_vorne' und 'vis.skip' zugleich: «Nur Grundlage» rechnet kein "
                "KI-Bild — ein Prompt fuer den KI-Schritt bestellt nichts.")
        maengel.append(satz)
        endgueltig.append(satz)
    elif vorne_wert:
        bestellt = [_materialwahl.BIBLIOTHEK[z["id"]]["prompt_en"] for z in prompt_zusaetze
                    if z.get("art") == "material" and z.get("id") in _materialwahl.BIBLIOTHEK
                    and z.get("weggelassen") != "material_der_variante"]
        if wunsch_nur_prompt:
            bestellt.insert(0, material_wunsch["wunsch"])
        # KEINE DOPPELUNG (auf-20261021-303, B3): Der Satz des Material-Knotens hinten
        # («exterior surfaces of <Stoff>») sagt, was vorne schon steht — er faellt weg und
        # bleibt mit `weggelassen` im Befund. Der Prompt des Bestellers bleibt Wort fuer Wort;
        # nennt er den Stoff schon, wird der Satz vorne kuerzer (`material_vorne_satz`).
        if bestellt:
            for z in prompt_zusaetze:
                if (z.get("art") == "material" and z.get("satz")
                        and _materialwahl.BIBLIOTHEK.get(z.get("id"), {}).get("prompt_en")
                        == bestellt[0]):
                    z["weggelassen"] = "material_vorne"
        rest = ", ".join([prompt_basis] + [
            z["satz"] for z in prompt_zusaetze if z.get("satz") and not z.get("vorne")
            and not z.get("weggelassen")])
        satz, stoffe = material_vorne_satz(prompt_basis, bestellt,
                                           rest_prompt=rest, hoechstens=nennungen)
        if satz is None and messschalter["material_vorne"]["herkunft"] == HERKUNFT_VORGABE:
            # Die VORGABE (Entscheid 126) ohne Stoff im Prompt und ohne Material-Knoten: Es
            # gibt nichts nach vorne zu stellen — kein leerer Zusatz, der Prompt bleibt.
            messschalter["material_vorne"] = {
                "herkunft": HERKUNFT_ENTFAELLT,
                "grund": "kein Stoff im Prompt und kein Material-Knoten"}
            for z in prompt_zusaetze:
                if z.get("weggelassen") == "material_vorne":
                    z.pop("weggelassen")
        else:
            eintrag = {"art": "material_vorne", "satz": satz, "vorne": True,
                       "stoffe": list(stoffe), "schon_im_prompt": False}
            if nennungen != MATERIAL_VORNE_HOECHSTENS:
                # Nur mit Schalter — ohne ihn bleibt der Eintrag Wort fuer Wort (346).
                eintrag["nennungen_hoechstens"] = nennungen
            prompt_zusaetze.append(eintrag)
    if nennungen != MATERIAL_VORNE_HOECHSTENS and not any(
            z.get("art") == "material_vorne" for z in prompt_zusaetze):
        warnungen.append(
            f"'vis.material_vorne_nennungen' ({nennungen}) wirkt nicht: Ohne Stoff vorne "
            f"('vis.material_vorne' aus oder kein Stoff) gibt es nichts zu kuerzen.")
    # DER GLASSATZ (Mac-Befund 23.10.2026, «haus-am-hang», auf-20261023-346) — Messschalter,
    # Vorgabe aus. VORNE, direkt hinter dem Stoff: Die Vorne-Schleife unten setzt jeden Satz an
    # den Anfang, der zuletzt gesetzte steht zuerst — darum VOR dem Eintrag des Stoffs eingefuegt.
    glas_wert = lies_glas_satz(vis, skip=schalter.get("skip"), maengel=maengel,
                               endgueltig=endgueltig)
    if glas_wert and not schalter.get("skip"):
        satz, schon = zusatz_glas(prompt_basis)
        stelle = next((i for i, z in enumerate(prompt_zusaetze)
                       if z.get("art") == "material_vorne"), len(prompt_zusaetze))
        prompt_zusaetze.insert(stelle, {"art": "glas", "satz": satz, "vorne": True,
                                        "schon_im_prompt": schon})
    # DIE AUTO-KAMERA MIT PARAMETERN (Entscheide 109/113, 20.10.2026).
    kameras_auto = kameras_auto_aus_szene(fremd.get("cameras_auto"), maengel=maengel,
                                          endgueltig=endgueltig)
    # Was als deutsches Kuerzel kam (B2) — ausserhalb von `kameras_auto`, damit der Schluessel
    # der Grundlage fuer «nNO» und «nNE» derselbe bleibt.
    kameras_umgedeutet = dict((kameras_auto or {}).pop("umgedeutet", None) or {})
    for de, en in kameras_umgedeutet.items():
        warnungen.append(f"Kamerakuerzel {de!r} (deutsch) als {en!r} gelesen.")
    if fremd.get("cameras_auto") is not None:
        widerspruch = kameras_auto_unvertraeglich(
            kameras=fremd.get("cameras", "auto"), skizze=fremd.get("skizze"),
            interior=fremd.get("interior"))
        maengel.extend(widerspruch)
        endgueltig.extend(widerspruch)
    if skizze_block is not None:
        maengel.extend(skizze_unvertraeglich(
            kameras=fremd.get("cameras", "auto"), interior=fremd.get("interior"),
            skip=schalter.get("skip"),
            # Eine weggelassene Punktwolke (R59) kommt nicht an — sie widerspricht nichts.
            kontext=None if kontext_weggelassen else fremd.get("context")))
    # Die Referenzbilder: Eine Zahl warf TypeError aus `list(...)`, ein Text zerfiel
    # still in einzelne Zeichen (23.09.2026).
    refs = stil.get("refs") or []
    if isinstance(refs, (list, tuple)):
        referenzen = list(refs)
        # EINE NICHT-LEERE LISTE WIRD ABGEWIESEN (B161, Blatt -02, 24.09.2026). Bis dahin
        # ging sie ohne Mangel durch und stand nur im Befund als «stehengeblieben»:
        # Kein Bildmodell unserer Kette nimmt nachweislich ein Referenzbild an (auf-123,
        # auf-137 V5), einen Erzeugungsweg dafür gibt es nicht. Drüben ist das Feld seit
        # dem 04.09.2026 aus dem Senden genommen — kommt es trotzdem, soll es ein Wort
        # hören (E75). Die leere Liste bestellt nichts und bleibt gültig.
        if referenzen:
            maengel.append(
                f"'style.refs' ({len(referenzen)} Referenz(en)) wird abgewiesen: Kein "
                f"Bildmodell unserer Kette nimmt nachweislich ein Referenzbild an "
                f"(gemessen: z-image-turbo und qwen-image-edit-2511 liefern mit und ohne "
                f"Eingangsbild dasselbe Bild), und einen Weg dafür gibt es nicht. "
                f"Abgewiesen statt uebergangen (E75 drueben, 19.09.2026).")
    else:
        referenzen = []
        maengel.append(
            f"'style.refs' ist {refs!r} und keine Liste. Als Text zerfiele es in "
            f"einzelne Zeichen; welche Bilder gemeint sind, raten wir nicht.")

    # DER PROMPT MIT DEN SAETZEN DER KNOTEN — nur, was er noch nicht traegt. Angefuegt NACH
    # dem Bauteilwaechter: Die Saetze stammen aus unseren Tabellen, nicht vom Besteller.
    render_prompt = prompt_basis
    for zusatz in prompt_zusaetze:
        if zusatz["satz"] and not zusatz.get("vorne") and not zusatz.get("weggelassen"):
            render_prompt = (f"{render_prompt}, {zusatz['satz']}" if render_prompt.strip()
                             else zusatz["satz"])
    # Der Stoff VORNE (Messschalter `vis.material_vorne`) — nach allen anderen Saetzen
    # gesetzt, damit er wirklich am Anfang steht.
    for zusatz in prompt_zusaetze:
        if zusatz["satz"] and zusatz.get("vorne"):
            render_prompt = (f"{zusatz['satz']}, {render_prompt}" if render_prompt.strip()
                             else zusatz["satz"])

    return {
        "geometrie": pfad,
        "format": fmt or None,
        "out": fremd.get("out"),
        "kameras": kameras,
        # Die Auto-Kamera mit Parametern (20.10.2026) — `None`: wie bisher die Einstellungen
        # des Abholers.
        "kameras_auto": kameras_auto,
        # Deutsche Kuerzel, die als englische gelesen wurden (auf-20261021-314, B2).
        "kameras_umgedeutet": kameras_umgedeutet,
        # `None` heisst hier NICHT GELESEN — dann steht der Grund unter `maengel`.
        "aufloesung": aufl[0],
        "hoehe": aufl[1],
        "samples": samples,
        "controlnet_staerke": treue,
        "prompt": render_prompt,
        "prompt_original": sprachbefund["original"],
        # Welche Saetze der Knoten der Heim-PC angefuegt hat (oder schon vorfand) — 20.10.2026.
        "prompt_zusaetze": tuple(prompt_zusaetze),
        # Die Messschalter aus Entscheid 117 (21.10.2026): False/None heisst aus — dann rechnet
        # der Heim-PC wie vorher. `farbabgleich` None: nicht gelesen (Mangel steht oben).
        "farbabgleich": farbabgleich,
        "bildeingang": bildeingang,
        # Entscheid 149: bewusst ohne Grundbild gerechnet — gekennzeichnet bis ins Ergebnis.
        "freies_bild": bool(freies_bild),
        # Mac-Probe 0.3.66: eine Variante (mit Grundlage oder `vis.variante`) — fuer die Staerke
        # und die Art im Vermerk (`abholer`, «Vorgabe fuer Varianten»).
        "ist_variante": bool(ist_variante),
        # Der Messschalter «Umriss halten» (Strang Treue): None heisst aus.
        "umriss_halten": umriss_halten,
        # Der Messschalter «Himmel sichtbar» (309): False/None heisst aus.
        "himmel_sichtbar": himmel_sichtbar,
        # Woher die drei Schalter der Varianten-Vorgabe kommen (Entscheid 126): je Name
        # {herkunft: bestellt|vorgabe|vorgabe_entfaellt|grundlage, grund?}; der Wert steht oben.
        "messschalter": messschalter,
        # Die Stimmung, wie gerechnet (ohne Pfad) — `None`: keine bestellt. Die Datei daneben
        # traegt den Pfad am Heim-PC und geht nur an den Runner, nie ins Ergebnis.
        "umgebung": (umgebung_block or {}).get("umgebung"),
        "umgebung_datei": (umgebung_block or {}).get("datei"),
        "umgebung_vorgaben": tuple((umgebung_block or {}).get("vorgaben") or ()),
        # Die Materialien je Art, wie gerechnet (ohne Pfad) — `None`: keine bestellt. Die
        # Karten am Heim-PC daneben gehen nur an den Runner (als JSON im Auftragsordner).
        "materialien": (material_block or {}).get("materialien"),
        "materialien_dateien": (material_block or {}).get("dateien"),
        "materialien_vorgaben": dict((material_block or {}).get("vorgaben") or {}),
        # Saetze ueber Dateien, die am Rechner fehlen (Entscheid 113) — fuer das Ergebnis.
        "fehlende_dateien": tuple(fehlende_dateien),
        "prompt_sprache": sprachbefund,
        "prompt_bauteile": tuple(bauteile),
        "stil_modus": wert_oder(stil, "mode", "none"),
        "stil_referenzen": referenzen,
        "backbone": bb["name"],
        "ueberspringen": schalter["skip"],
        "hochskalieren": schalter["upscale"],
        # Owner-Grundsatz Nr. 85: eine gerechnete Grundlage wiederverwenden, und ein fester
        # Startwert fuer die ganze Serie. `None` = nicht bestellt.
        "grundlage": grundlage,
        "seed": seed,
        # N6 (22.10.2026): Die bestellte Grundlage, die NICHT wiederverwendet wird, weil die
        # Variante eine andere Stimmung traegt (`stimmung_der_variante`) — ihr Auftrag liefert
        # das Modell, wenn die Bestellung keines mitbringt. `None`: nichts verworfen.
        "grundlage_verworfen": ((variante_stimmung or {}).get("grundlage_verworfen")
                                or (material_wunsch or {}).get("grundlage_verworfen")),
        "stimmung_der_variante": variante_stimmung,
        # Befund 337 (22.10.2026): der Fassadenstoff der Variante und was damit geschah —
        # `None`: kein Stoffwunsch (oder keine Variante). Im Ergebnis unter
        # `angewandt.variante.material_wunsch`.
        "material_der_variante": material_wunsch,
        # Entscheid 104: 'vorschau' | 'voll' | None (nicht bestellt — gilt 'voll').
        "guete": guete,
        # Knoten «Umfeld» (24.10.2026): {kategorien, dichte, seed, anzahl?} — `None`: nicht
        # bestellt. Was gestellt wird, plant und laedt der Abholer (`umfeld.plane_fuer_glb`).
        "umfeld": umfeld_wunsch,
        "sonne": sonne,
        # Bestellte Ebenen (E124, Schritt 1, 29.09.2026): Tupel aus EBENEN_ARTEN, leer =
        # keine bestellt.
        "ebenen": ebenen,
        "innenraum": innenraum,
        "innen_bestellt": innen_bestellt,
        "gelaende_erwartet": gelaende,
        # `None` heisst: keine Umgebung bestellt — oder eine Punktwolke ohne Splat-Felder,
        # dann steht sie unter `kontext_weggelassen` (R59).
        "kontext": kontext_block,
        "kontext_weggelassen": kontext_weggelassen,
        # `None` heisst: keine Skizze bestellt (Entscheid 96).
        "skizze": skizze_block,
        # Was JEDEN Auftrag gleich trifft — getrennt von dem, was DIESEN betrifft.
        #
        # **Der Anlass ist eine Zaehlung** (26.08.2026): `tools/abholen.py` zeigte
        # `warnungen[:3]`, und genau drei Warnungen aus dieser Funktion feuerten bei
        # jedem gewoehnlichen Auftrag. Sie fuellten also alle drei Plaetze — eine echte,
        # auftragsspezifische Warnung, die im Code SPAETER steht, war damit unsichtbar.
        # Die immer feuernde Warnung verdraengt nicht nur sich selbst, sie VERDECKT die
        # anderen.
        #
        # Dieselbe Trennung wie in `abholer._kompositionszeilen`: Was alle betrifft,
        # steht einmal da. Und es verschwindet nicht — es steht nur woanders.
        "vertragsvorgaben": tuple(vorgaben),
        "warnungen": tuple(warnungen),
        "maengel": tuple(maengel),
        # DIE MAENGEL, DIE KEIN WARTEN HEILT (auf-20261020-290, Befund 5) — eine Teilmenge
        # von `maengel`: Widersprueche in der Bestellung selbst. Der Abholer beendet einen
        # solchen Auftrag mit `error` und Satz; alle anderen Maengel lassen ihn wie bisher
        # mit Grund auf `queued` liegen.
        "maengel_endgueltig": tuple(endgueltig),
    }


# --------------------------------------------------------------------------------------
# Was von der Bestellung wirklich ankommt — und was nicht
# --------------------------------------------------------------------------------------
#
# **Der Anlass ist ein Fehler, den dieses Projekt am 23.08.2026 zweimal an einem Tag
# gemacht hat, beide Male an derselben Stelle: an der Naht.** Die Brennweite war im Kern
# längst einstellbar und kam an der Aussenkante trotzdem nicht durch — zwei fest
# verdrahtete `28.0` standen im Weg. Der Geländestand ebenso. Beide Male hiess es
# «einstellbar», und beide Male stimmte es im Modul und nicht im Betrieb.
#
# **Einstellbar ist ein Versprechen, das man an der Naht prüft, nicht am Modul.** Diese
# Tabelle ist die ausführbare Form davon: Jedes Feld, das :func:`lies_szene` aus der
# Bestellung liest, steht in genau einer der beiden Listen — es kommt an, oder es bleibt
# stehen und der Grund steht dabei. Ein neues Feld im fremden Vertrag kann damit nicht
# mehr stillschweigend ins Leere laufen; es fällt beim ersten Testlauf auf.

#: Felder, die unsere Kette wirklich erreichen — mit der Stelle, an der sie ankommen.
DURCHGEREICHT = {
    "ebenen": "abholer → bruecke.schreibe_ergebnis(ebenen=…) → render-result 'ebenen'",
    "geometrie": "abholer: Pfad der glb",
    "format": "lies_szene selbst — unbekannte Formate werden als Mangel abgelehnt; "
              "'ifc' waehlt seit 22.09.2026 in bruecke.lies_auftrag model.ifc und in "
              "abholer.verarbeiter die Umwandlung IFC → glb (seams.ifc_zu_glb)",
    "out": "abholer: Ausgabeverzeichnis",
    "kameras": "abholer.verarbeiter → Kameraaufgaben",
    # Seit 20.10.2026 (Knoten «Kamera»): Richtungen, Augenhoehe, Brennweite, Abstand und
    # Perspektive je Auftrag statt je Abholer.
    "kameras_auto": ("abholer.verarbeiter → Aufgaben je Richtung, seams.glb_zu_multipass("
                     "brennweite/augenhoehe/deckungsgrad/abstand_fest_m/kamera_modus) → "
                     "blender_depth_stage → kameras.kamerasatz; render-result "
                     "'angewandt.cameras_auto'"),
    "aufloesung": "seams.glb_zu_multipass(aufloesung=…)",
    "hoehe": "seams.glb_zu_multipass(hoehe=…)",
    "samples": "seams.glb_zu_multipass(samples=…)",
    "controlnet_staerke": "render.RenderAuftrag(controlnet_staerke=…)",
    "backbone": "render.RenderAuftrag(backbone=…)",
    "prompt": "render.RenderAuftrag(prompt=…)",
    # Seit 20.10.2026 (Entscheide 110/113): die Saetze der Knoten, die angefuegt wurden.
    "prompt_zusaetze": "lies_szene → 'prompt'; befund.json und render-result 'angewandt'",
    # Seit 21.10.2026 (Entscheid 117): zwei Messschalter, nicht im Vertrag.
    "farbabgleich": ("abholer.farbabgleich_der_kamera → das gelieferte KI-Bild; Vermerk am "
                     "Kameraurteil in befund.json; im render-result Satz in "
                     "'qa.verdict.hinweise' und 'angewandt.farbabgleich' (auf-20261021-298 B1)"),
    "freies_bild": ("abholer.angewandt_der_szene → render-result 'angewandt.freies_bild' und "
                    "'freies_bild: true', Satz in 'qa.verdict.hinweise' (Entscheid 149)"),
    "ist_variante": ("bildeingang_vorgabe_fuer (0,7 statt 0,5) und abholer → Vermerk "
                     "'art: variante' am Bildeingang, Satz «Vorgabe fuer Varianten» in "
                     "'qa.verdict.hinweise' (Mac-Probe 0.3.66, vis.variante)"),
    "bildeingang": ("render.RenderAuftrag(bildeingang_staerke=…); im render-result Satz in "
                    "'qa.verdict.hinweise' und 'angewandt.bildeingang' (auf-20261021-298 B1)"),
    # Seit 21.10.2026 (Strang Treue): Messschalter, nicht im Vertrag. `material_vorne` reist
    # als Satz in `prompt_zusaetze` (mit `vorne`) und damit im Prompt.
    "himmel_sichtbar": ("abholer.umgebung_einstellungen → umgebung_licht {himmel_sichtbar} → "
                        "blender_depth_stage._welt_setzen (Kamerastrahl sieht das Himmelsbild); "
                        "Bericht 'umgebung.hintergrund.art' himmelsbild"),
    "kameras_umgedeutet": "abholer.angewandt_der_szene → 'angewandt.cameras_auto.umgedeutet'",
    "messschalter": ("abholer.angewandt_der_szene → render-result 'angewandt.messschalter' "
                     "{<name>: {wert, herkunft, grund?}} (Entscheid 126)"),
    "umriss_halten": ("abholer.umriss_halten_der_kamera (nachher) bzw. render.RenderAuftrag("
                      "umriss_halten_png=…) (im_lauf); Vermerk am Kameraurteil und Satz in "
                      "'qa.verdict.hinweise' (dazu der Satz des Bildmodells) und "
                      "'angewandt.umriss_halten' (auf-20261021-303 B2)"),
    "umgebung": ("abholer.verarbeiter → GRUNDLAGE_MUSS_PASSEN und render-result "
                 "'angewandt.environment'"),
    "umgebung_datei": ("abholer.verarbeiter → seams.glb_zu_multipass(umgebung_hdr=…) → "
                       "blender_depth_stage --umgebung-hdr/--umgebung-staerke/"
                       "--umgebung-drehung (/--umgebung-weiss)"),
    "umgebung_vorgaben": "abholer.angewandt_der_szene → render-result 'angewandt'",
    # Seit 20.10.2026 (Knoten «Material», Entscheide 107/111/113).
    "materialien": ("abholer.verarbeiter → GRUNDLAGE_MUSS_PASSEN und render-result "
                    "'angewandt.materialien'"),
    "materialien_dateien": ("abholer.materialwahl_ablegen → materialwahl.json im "
                            "Auftragsordner → seams.glb_zu_multipass(materialien_json=…) → "
                            "blender_depth_stage --materialien → _materialien_setzen"),
    "materialien_vorgaben": "abholer.angewandt_der_szene → render-result 'angewandt'",
    "fehlende_dateien": ("abholer.hole_einen → render-result mit lieferstatus "
                         "'fehlgeschlagen' und lieferstatus_grund"),
    "prompt_original": "befund.json",
    "prompt_sprache": "befund.json und befund_kurz",
    "prompt_bauteile": "befund.json und befund_kurz",
    "vertragsvorgaben": "tools/abholen.py: einmal pro Lauf, nicht je Auftrag",
    "warnungen": "Antwort des Auftrags",
    "maengel": "halten den Lauf auf",
    # Seit 20.10.2026 (auf-20261020-290, Befund 5): die Teilmenge, die den Auftrag beendet.
    "maengel_endgueltig": "abholer.hole_einen: beenden den Auftrag mit error und Satz",
    # Seit 26.08.2026 — vorher stand es in STEHENGEBLIEBEN, und der Abholer meldete das
    # von sich aus: «BESTELLT UND NICHT AUSGEFUEHRT». Im Lauf vom 25.08. wurde es dann
    # belegt (auf-vis-20260825-15, Posten 2): Wer abbestellt, bekommt geliefert — und
    # zahlt die GPU-Zeit.
    # SEIT DEM 20.10.2026 «NUR GRUNDLAGE» (Demolauf Nr. 83, Auflage 3 des Integrators): Vom
    # 26.08. bis 20.10. hiess es hier «wird NICHT gerendert» — ihr Vertrag meinte aber
    # «ohne KI-Schritt» (die lineart-Kopplung in render-scene.ts). Das Haekchen «nur Cycles»
    # bekam darum gar nichts.
    "ueberspringen": "abholer.verarbeiter: nur Grundlage — Cycles und Ebenen, KEIN "
                     "Bildmodell; das Cycles-Bild ist das gelieferte Bild",
    "grundlage": "abholer.verarbeiter: Kameras und Multipass aus der abgelegten "
                 "Grundlage (abholer.lies_grundlage), kein Blender-Lauf",
    "seed": "abholer.verarbeiter: genau dieser Startwert statt der Auswahl aus drei",
    "grundlage_verworfen": ("bruecke.lies_auftrag: Modell des Auftrags dieser Grundlage, wenn "
                            "die Variante eine eigene Stimmung (N6) oder einen eigenen "
                            "Fassadenstoff (Befund 337) bekommt"),
    "stimmung_der_variante": "lies_szene selbst: Licht und Satz in 'warnungen' (N6)",
    "material_der_variante": ("lies_szene selbst: Materialwahl der Fassade und Satz in "
                              "'warnungen'; abholer.angewandt_der_szene → "
                              "angewandt.variante.material_wunsch (Befund 337)"),
    "umfeld": ("abholer.umfeld_vorbereiten → umfeld.plane_fuer_glb, umfeld.hole_plan → "
               "umfeld.json im Auftragsordner → seams.glb_zu_multipass(umfeld_json=…) → "
               "blender_depth_stage --umfeld → _umfeld_laden; GRUNDLAGE_MUSS_PASSEN und "
               "render-result 'angewandt.umfeld'"),
    "guete": ("abholer.verarbeiter: 'vorschau' rechnet VORSCHAU_BACKBONE mit dessen "
              "vorschau_schritte, einem Startwert und verkleinerten Steuerbildern; "
              "render-result 'guete' (Entscheid 104)"),
    # Seit 26.08.2026 — vorher der GEFAEHRLICHSTE der stehengebliebenen Felder, weil das
    # Bild danach richtig AUSSAH (auf-vis-20260825-15 Posten 5.3).
    "sonne": ("seams.glb_zu_multipass(sonne=…) → blender_depth_stage --sonne-hoehe/-azimut/"
              "-konvention/-staerke/-kelvin/-winkel"),
    # Seit 22.09.2026 (auf-104): `interior` {rooms: "auto"}. Nur ohne mitgesandte
    # Kameras gesetzt — mit ihnen gelten diese, siehe `_lies_interior`.
    "innenraum": "abholer.verarbeiter: Raeume aus der IFC (seams.ifc_raeume), EINE "
                 "Kameraaufgabe aus raumkamera.waehle (auge, blick_auf, Brennweite des "
                 "Standpunkts) → seams.glb_zu_multipass auf der umgewandelten glb; "
                 "Vermerk am Kameraurteil (URTEIL_INNENANSICHT) und in verdict.reason",
    # Seit 23.09.2026: dass `interior` bestellt war, auch MIT Kameraliste — die Form, in
    # der KosmoOrbit jede Innenbestellung sendet (auf-91 V1). Es wird kein Standpunkt
    # gerechnet; nur der Vermerk reist mit.
    "innen_bestellt": "abholer.verarbeiter: Vermerk (standpunkt 'mitgesandt') an jedem "
                      "Kameraurteil einer mitgesandten Kamera → urteil.json, befund.json "
                      "und verdict.reason (innenansicht_satz)",
    # Seit 22.09.2026: `gelaende` (auf-67), dreiwertig. Schlaegt den prozessweiten
    # Schalter des Abholers, weil die Aussage je Szene gilt.
    "gelaende_erwartet": "abholer.verarbeiter → maske (gelaende_erwartet=…)",
    # Seit 08.10.2026 (Entscheid 76): `context` {kind: splat, ply, transform, fit, …}.
    "kontext": "abholer.verarbeiter → seams.glb_zu_multipass(kontext_ply=…, "
               "kontext_matrix=…) → blender_depth_stage --kontext-ply/--kontext-matrix; "
               "Vermerk am Kameraurteil (URTEIL_KONTEXT) → verdict.hinweise, befund.json",
    # Seit Geraeteprobe R59 (23.10.2026): eine Punktwolke ohne 3DGS-Felder als `context`.
    "kontext_weggelassen": "lies_szene selbst: Satz in 'warnungen'; abholer.angewandt_der_szene "
                           "→ angewandt.kontext_weggelassen → verdict.hinweise "
                           "(ergebnis_saetze_der_szene); an den Multipass geht nichts",
    # Seit 15.10.2026 (Entscheid 96): `skizze` {quelle: mappe, name, anweisung?}.
    "skizze": "abholer.verarbeiter → arbeitsgang.rechne_skizze(Mappe aus "
              "knotenweg.mappe_des_auftrags, name, anweisung=…, backbone=…); Vermerk "
              "URTEIL_SKIZZE → verdict.reason/hinweise, befund.json",
}

#: Felder, die der Betreiber setzen **kann** und die heute **nichts** bewirken.
#:
#: Jeder Eintrag trägt, was fehlt — nicht bloss, dass etwas fehlt. Ein «wird nicht
#: unterstützt» ohne den nächsten Schritt ist eine Sackgasse; mit ihm ist es eine Aufgabe.
STEHENGEBLIEBEN = {
    "hochskalieren": {
        "fremd": "upscale",
        "neutral": False,
        "grund": "Es gibt keinen Hochskalierer in dieser Kette. Ein `upscale: true` "
                 "liefert dasselbe Bild wie `false`.",
        "noetig": "Ein Hochskalierer mit permissiver Lizenz (Regel 1) — und ein Entscheid "
                  "darüber, ob die Geometrie-QA auf dem hochskalierten Bild oder auf dem "
                  "ursprünglichen gemessen wird. Beides ist offen.",
    },
    "stil_modus": {
        "fremd": "style.mode",
        "neutral": "none",
        "grund": "Die Stil-QA läuft in dieser Kette nicht. Das ist ausdrücklich "
                 "entschieden und nicht vergessen: Sie bräuchte ein Referenzset, das uns "
                 "gehört, und die bisherigen Referenzen sind fremde Bildschirmfotos.",
        "noetig": "Ein eigenes Referenzset. `als_ergebnis` schreibt bei fehlendem "
                  "Stil-Urteil bereits «ungeprüft» statt «durchgefallen» — die Lücke ist "
                  "also im Ergebnis sichtbar, nur eben nicht in der Bestellung.",
    },
    "stil_referenzen": {
        "fremd": "style.refs",
        "neutral": [],
        "grund": "Referenzbilder werden aus der Bestellung gelesen und danach von "
                 "niemandem. Anders als bei `stil_modus` schickt der Betreiber hier "
                 "eigene Dateien mit — er hat also Arbeit hineingesteckt, die verfällt.",
        "noetig": "Dasselbe eigene Referenzset wie bei `stil_modus`, und zusätzlich ein "
                  "Entscheid, wie fremde Referenzbilder überhaupt zu uns gelangen sollen: "
                  "Regel 3 verbietet Bilder im Repo, ein Pfad auf ihrem Rechner nützt uns "
                  "nichts. Diese Frage ist offen und gehört in ihren Vertrag.",
    },
}


def stehengebliebene_felder(szene: dict) -> tuple[dict, ...]:
    """Welche Felder dieser **einen** Bestellung ins Leere laufen.

    Gemeldet wird nur, was der Betreiber auch wirklich **gesetzt** hat. Ein Feld auf
    seinem neutralen Wert ist keine unerfüllte Bestellung, und eine Warnung, die bei
    jedem Auftrag erscheint, ist nach dem dritten Mal keine mehr — das ist am
    23.08.2026 an der Kompositionsprüfung gemessen worden (zwölf von zwölf Kameras
    trugen dieselben zwei Warnungen).

    Returns:
        Je betroffenem Feld ``{feld, wert, grund, noetig}``, in der Reihenfolge der
        Tabelle. Leer, wenn die Bestellung nichts verlangt, was wir nicht liefern.
    """
    if not isinstance(szene, dict):
        raise SzenenError(f"szene ist kein Wörterbuch: {type(szene).__name__}")
    offen = []
    for feld, eintrag in STEHENGEBLIEBEN.items():
        wert = szene.get(feld, eintrag["neutral"])
        if wert == eintrag["neutral"]:
            continue
        offen.append({"feld": feld, "wert": wert,
                      "grund": eintrag["grund"], "noetig": eintrag["noetig"]})
    return tuple(offen)


# --------------------------------------------------------------------------------------
# Unser Ergebnis in ihren Vertrag
# --------------------------------------------------------------------------------------

# ── Der Lieferstatus — am Auftrag und je Kamera (23.09.2026) ─────────────────────────
#
# **Der Befund** (Teilantwort von KosmoOrbit auf `auf-20260919-119`, V3/V4, uebertragen
# am 23.09.2026): Ihr Ergebnisvertrag traegt seit dem 01.09.2026 ein Feld `lieferstatus`
# mit `lieferstatus_grund` — am AUFTRAG, mit der Vorgabe `'geliefert'`. Niemand setzte
# es, auch wir nicht. Jedes Ergebnis, das wir schrieben, behauptete damit drueben eine
# vollstaendige Lieferung, auch eines mit null Bildern.
#
# **Was sie brauchen:** dieselbe Auskunft JE KAMERA in `qa_je_kamera[]`, mit
# `bilder_soll` und `bilder_ist` als zwei Zahlen nebeneinander. Die Namen durften wir
# vorschlagen, die Ebene nicht. Wir uebernehmen ihre Namen woertlich — ein zweiter
# Name fuer dieselbe Sache waere eine Uebersetzung, die jemand pflegen muss.
#
# **Solange sie die Felder je Kamera nicht gebaut haben**, streift ihr Einlesen sie ab
# (`qa_je_kamera` ist dort `z.object({kamera, geometry, style})`, nicht strikt —
# erg-20260917-49, render-result.ts 366-393). Darum steht die Auskunft auch im
# `lieferstatus_grund` des Auftrags, der heute schon ankommt.

#: Die drei Werte von `lieferstatus` in ihrem Vertrag (`Lieferstatus = z.enum([...])`,
#: erg-20260917-37 F3). Woertlich — ein anderer Wert wird drueben abgewiesen.
LIEFERSTATUS_GELIEFERT = "geliefert"
LIEFERSTATUS_UEBERSPRUNGEN = "uebersprungen"
LIEFERSTATUS_FEHLGESCHLAGEN = "fehlgeschlagen"
LIEFERSTATUS = (LIEFERSTATUS_GELIEFERT, LIEFERSTATUS_UEBERSPRUNGEN,
                LIEFERSTATUS_FEHLGESCHLAGEN)

#: Die vier Felder, die ein Eintrag in `qa_je_kamera` seit dem 23.09.2026 traegt, wenn
#: der Aufrufer die Lieferung kennt (auf dem Produktweg: `abholer._lieferung_der_kamera`).
#: Die Namen sind ihre (V4); die Ebene je Kamera ist ihre Vorgabe.
FELDER_LIEFERUNG = ("lieferstatus", "lieferstatus_grund", "bilder_soll", "bilder_ist")


def _bilderzahl(wert, feld: str, name) -> int | None:
    """Eine Bilderzahl — eine ganze Zahl ab null oder ``None`` (NICHT GEZAEHLT).

    ``bool`` zaehlt nicht (``True`` waere sonst ein Bild), und eine Kommazahl auch nicht:
    Ein halbes Bild gibt es nicht, und ``1.0`` statt ``1`` verriete einen Rechenweg, der
    hier nichts zu suchen hat.
    """
    if wert is None:
        return None
    if isinstance(wert, bool) or not isinstance(wert, int) or wert < 0:
        raise SzenenError(
            f"Kamera {name!r}: {feld} ist {wert!r} — erwartet ist eine ganze Zahl ab 0 "
            f"oder null (nicht gezaehlt), nie eine erfundene Null.")
    return wert


def _lieferung_je_kamera(eintrag: dict) -> dict | None:
    """Die vier Lieferfelder eines Eintrags — geprueft, oder ``None``, wenn keines da ist.

    ``None`` heisst: Der Aufrufer hat ueber die Lieferung nichts gesagt. Dann fehlen die
    Felder im Eintrag ganz, statt mit erfundenen Werten dazustehen — und der Auftrag
    meldet ``lieferstatus: null`` mit Grund (siehe :func:`_lieferstatus_des_auftrags`).

    **Was angenommen wird, muss stimmen** — sonst laut, nicht still:

    * ``lieferstatus`` ist einer der drei Werte oder ``None`` (nicht festgestellt).
    * ``geliefert`` genau dann, wenn ``bilder_ist == bilder_soll > 0``. Ein
      «geliefert» mit null Bildern war die Luege der fremden Vorgabe; ein
      «fehlgeschlagen» bei vollstaendiger Lieferung waere dieselbe Luege umgekehrt.
    * ``lieferstatus_grund`` ist Pflicht, sobald nicht ``geliefert`` (ihr
      ``superRefine``).
    """
    if not any(feld in eintrag for feld in FELDER_LIEFERUNG):
        return None
    name = eintrag.get("kamera")
    status = eintrag.get("lieferstatus")
    if status is not None and status not in LIEFERSTATUS:
        raise SzenenError(
            f"Kamera {name!r}: lieferstatus {status!r} ist keiner der drei Werte ihres "
            f"Vertrags {LIEFERSTATUS}. Drueben wuerde das ganze Ergebnis abgewiesen.")
    soll = _bilderzahl(eintrag.get("bilder_soll"), "bilder_soll", name)
    ist = _bilderzahl(eintrag.get("bilder_ist"), "bilder_ist", name)
    grund = eintrag.get("lieferstatus_grund")
    grund = "" if grund is None else str(grund)
    vollstaendig = soll is not None and ist is not None and soll == ist and soll > 0
    if status == LIEFERSTATUS_GELIEFERT and not vollstaendig:
        raise SzenenError(
            f"Kamera {name!r}: 'geliefert' bei bilder_soll={soll!r}, bilder_ist={ist!r}. "
            f"Geliefert heisst: alle bestellten Bilder da, und mindestens eines — genau "
            f"die Behauptung, die ihre Vorgabe bis zum 23.09.2026 still machte.")
    if status in (LIEFERSTATUS_UEBERSPRUNGEN, LIEFERSTATUS_FEHLGESCHLAGEN) and vollstaendig:
        raise SzenenError(
            f"Kamera {name!r}: {status!r}, obwohl {ist} von "
            f"{sprache.anzahl(soll, 'Bild', 'Bildern')} da sind. "
            f"Ein vollstaendig geliefertes Bild als nicht geliefert zu melden, ist "
            f"dieselbe Unwahrheit in der anderen Richtung.")
    if status != LIEFERSTATUS_GELIEFERT and not grund.strip():
        raise SzenenError(
            f"Kamera {name!r}: lieferstatus {status!r} ohne lieferstatus_grund. Ihr "
            f"Vertrag verlangt den Satz, sobald nicht geliefert — und ohne ihn weiss "
            f"niemand, was zu tun ist.")
    return {"lieferstatus": status, "lieferstatus_grund": grund,
            "bilder_soll": soll, "bilder_ist": ist}


def _lieferstatus_des_auftrags(saetze, *, uebersprungen: bool,
                               anzahl_bilder: int) -> tuple[str | None, str]:
    """``(lieferstatus, lieferstatus_grund)`` des ganzen Auftrags.

    **Geliefert nur, wenn JEDE Kamera geliefert hat.** Sonst griffe ihre Vorgabe
    `'geliefert'` in anderer Form wieder: Ein Auftrag mit acht von zwoelf Bildern
    hiesse geliefert.

    * ``skip: true`` → ``uebersprungen`` — ihr Sinn des Wortes (erg-20260917-37 F3).
    * eine Kamera ``fehlgeschlagen`` → der Auftrag ``fehlgeschlagen``.
    * sonst mindestens eine Kamera ``geliefert`` und der Rest ``uebersprungen`` (heute nur
      die Zwillingsansicht) → der Auftrag ``geliefert``, **mit Grund**, der die Zwillinge
      nennt. Entscheid vom 23.09.2026: «uebersprungen» heisst am Auftrag bei ihnen «fand
      insgesamt nicht statt» — das stimmt nicht, wenn Bilder kamen; und die Ansicht eines
      Zwillings IST geliefert, mit dem Bild seines Vorbilds. Bis dahin hiess gerade der
      einfachste Demofall (ein symmetrischer Quader) am Auftrag «uebersprungen».
    * nur ``uebersprungen`` (kein Bild) → der Auftrag ``uebersprungen``.
    * ``None`` — NICHT FESTGESTELLT —, wenn keine Kamera eine Lieferung meldet, eine
      Kamera ``lieferstatus: None`` traegt, oder die Bilderzahlen der Kameras nicht mit
      der Bildliste uebereinstimmen. Das ist die dritte Antwort und keine Vorgabe:
      ``null`` besteht ihr Schema vermutlich nicht, und ein Ergebnis, das dort laut
      abgewiesen wird, ist besser als eines, das still «geliefert» sagt.
    """
    if uebersprungen:
        return LIEFERSTATUS_UEBERSPRUNGEN, (
            "Abbestellt (skip: true): nichts gerechnet, kein Bild bestellt.")
    lieferungen = [(s["kamera"], s) for s in (saetze or ()) if "lieferstatus" in s]
    if not lieferungen or len(lieferungen) != len(saetze or ()):
        return None, (
            f"NICHT FESTGESTELLT: {len(lieferungen)} von "
            f"{sprache.anzahl(len(saetze or ()), 'Kamera', 'Kameras')} "
            f"melden eine Lieferung, {anzahl_bilder} Bild(er) in der Liste — ohne eine "
            f"Meldung je Kamera ist nicht zu sagen, ob alles Bestellte da ist.")
    offen = [name for name, s in lieferungen if s["lieferstatus"] is None]
    if offen:
        return None, (f"NICHT FESTGESTELLT: Die Lieferung der Kamera(s) "
                      f"{', '.join(map(repr, offen))} ist nicht festgestellt.")
    soll = [s["bilder_soll"] for _, s in lieferungen]
    ist = [s["bilder_ist"] for _, s in lieferungen]
    if None not in ist and sum(ist) != anzahl_bilder:
        return None, (
            f"NICHT FESTGESTELLT: Die Kameras melden {sum(ist)} Bild(er), die Bildliste "
            f"traegt {anzahl_bilder}. Zwei Zahlen fuer dieselbe Lieferung, und eine ist "
            f"falsch.")
    status = [s["lieferstatus"] for _, s in lieferungen]
    if all(x == LIEFERSTATUS_GELIEFERT for x in status):
        return LIEFERSTATUS_GELIEFERT, ""
    if LIEFERSTATUS_FEHLGESCHLAGEN in status:
        gesamt = LIEFERSTATUS_FEHLGESCHLAGEN
    elif LIEFERSTATUS_GELIEFERT in status:
        gesamt = LIEFERSTATUS_GELIEFERT
    else:
        gesamt = LIEFERSTATUS_UEBERSPRUNGEN

    def zahl(werte):
        return "unbekannt" if None in werte else str(sum(werte))

    fehlend = "; ".join(f"{name} {s['lieferstatus']}: {s['lieferstatus_grund']}"
                        for name, s in lieferungen
                        if s["lieferstatus"] != LIEFERSTATUS_GELIEFERT)
    return gesamt, (
        f"{status.count(LIEFERSTATUS_GELIEFERT)} von "
        f"{sprache.anzahl(len(status), 'Kamera', 'Kameras')} geliefert, "
        f"{zahl(ist)} von {sprache.anzahl(zahl(soll), 'Bild', 'Bildern')} — {fehlend}")


#: Der Anteil voll weisser Bildpunkte am Haus im Cycles-Bild (auf-20261020-292, B1) — im
#: ``qa``-Block des Laufs (die höchste Kamera) und je Kamera. Fehlt, wenn nicht gemessen
#: (ohne Stimmung, oder nicht lesbar) — ein ``null`` bestünde ihr ``.optional()`` nicht.
FELD_UEBERSTRAHLT = "ueberstrahlt_anteil"


def _ueberstrahlt_von(urteil):
    befund = (urteil or {}).get("ueberstrahlt") if isinstance(urteil, dict) else None
    anteil = befund.get("anteil") if isinstance(befund, dict) else None
    return anteil if isinstance(anteil, (int, float)) and not isinstance(anteil, bool) \
        else None


def _ueberstrahlt_eintragen(qa: dict, geometrie_urteil, je_kamera, hinweise: list) -> None:
    """``qa.ueberstrahlt_anteil``: je Kamera gemessen, für den Lauf die höchste — mit Satz,
    wenn das Ziel (weniger als 1 % voll weiss am Haus) verfehlt ist."""
    from . import belichtung as _belichtung  # noqa: PLC0415
    werte = []
    for eintrag in je_kamera or ():
        if isinstance(eintrag, dict):
            wert = _ueberstrahlt_von(eintrag.get("geometrie_urteil") or eintrag.get("stimmung"))
            if wert is not None:
                werte.append((wert, eintrag.get("kamera")))
    if not werte:
        wert = _ueberstrahlt_von(geometrie_urteil)
        if wert is not None:
            werte.append((wert, (geometrie_urteil or {}).get("kamera")))
    if not werte:
        return
    hoechster, kamera = max(werte, key=lambda w: w[0])
    qa[FELD_UEBERSTRAHLT] = hoechster
    if hoechster >= _belichtung.UEBERSTRAHLT_ZIEL:
        hinweise.append(
            f"UEBERSTRAHLT: Im Cycles-Bild der Kamera {kamera!r} sind {hoechster * 100:.1f} % "
            f"des Hauses voll weiss (Ziel unter {_belichtung.UEBERSTRAHLT_ZIEL * 100:.0f} %) — "
            f"dort traegt das Bild keine Zeichnung. Belichtung der Stimmung pruefen.")


#: Der Kontrast Haus – Hintergrund im Cycles-Bild (auf-20261020-293, Punkt 1): Grauwert des
#: Hauses minus Hintergrund daneben, 0..255. Im ``qa``-Block der Lauf mit dem KLEINSTEN
#: Betrag (die Kamera, auf der das Haus am schlechtesten zu sehen ist), und je Kamera. Fehlt,
#: wenn nicht gemessen — wie ``ueberstrahlt_anteil`` kein ``null``.
FELD_KONTRAST = "kontrast_haus_hintergrund"
#: Der Satz, wenn sich das Haus kaum abhebt.
SATZ_KAUM_SICHTBAR = "HAUS KAUM SICHTBAR"
#: Derselbe Kontrast am KI-BILD (Ergebnis auf-20261022-334): ``qa.kontrast_haus_hintergrund``
#: misst das Cycles-Bild, auch bei einer KI-Variante. Daneben, nicht statt — dieselbe Formel,
#: Maske und ID-Pass, am gelieferten KI-Bild. Im ``qa``-Block der kleinste Betrag, und je
#: Kamera; fehlt, wenn nicht gemessen. Kein Satz, keine Warnung.
FELD_KONTRAST_KI = "kontrast_haus_hintergrund_ki"
#: Wo der Abholer ihn am Kameraurteil ablegt.
URTEIL_KONTRAST_KI = "kontrast_ki"
#: «Fenster gehalten» am KI-Bild (Mac-Befund 23.10.2026, ``varianten.fenster_gehalten``) — wo
#: der Abholer den Befund am Kameraurteil ablegt. Fehlt ohne Glas im ID-Pass.
URTEIL_FENSTER = "fenster"


#: Der Kontrast AM UMRISS (Ergebnis auf-20261023-343, 5; ``belichtung.kontrast_am_umriss``):
#: Haus innen gegen Hintergrund aussen an jeder Kantenstelle, im Betrag gemittelt (0..255,
#: immer positiv), an derselben Kamera
#: wie ``qa.kontrast_haus_hintergrund``. **Seit Ergebnis auf-20261023-344 (K4) hängt die
#: Warnung «HAUS KAUM SICHTBAR» an dieser Zahl** (je Kamera, ``belichtung.haus_kaum_sichtbar``,
#: Schwelle ``belichtung.KONTRAST_UMRISS_SCHWELLE``); der Mittelwert bleibt im ``qa``-Block
#: und gilt nur noch dort, wo der Umriss fehlt.
FELD_KONTRAST_UMRISS = "kontrast_umriss_haus_hintergrund"


def _kontrast_von(urteil):
    befund = (urteil or {}).get("kontrast") if isinstance(urteil, dict) else None
    wert = befund.get("kontrast") if isinstance(befund, dict) else None
    return wert if isinstance(wert, (int, float)) and not isinstance(wert, bool) else None


def _umriss_von(urteil):
    """Der Betrag des Kontrasts am Umriss (``kontrast.umriss.betrag``) — oder ``None``."""
    befund = (urteil or {}).get("kontrast") if isinstance(urteil, dict) else None
    umriss = befund.get("umriss") if isinstance(befund, dict) else None
    wert = umriss.get("betrag") if isinstance(umriss, dict) else None
    return wert if isinstance(wert, (int, float)) and not isinstance(wert, bool) else None


def _kontrast_eintragen(qa: dict, geometrie_urteil, je_kamera, hinweise: list) -> None:
    """``qa.kontrast_haus_hintergrund``: je Kamera gemessen, für den Lauf der kleinste Betrag
    (dazu der Umriss derselben Kamera) — mit Satz «HAUS KAUM SICHTBAR», wenn eine Kamera
    kaum sichtbar ist.

    **Geurteilt wird je Kamera am Umriss** (Ergebnis auf-20261023-344, K4: mittags Mittel
    −19,6 / −5,0, Umriss 51,7 / 54,3, von Auge klar sichtbar). Nur wo der Umriss fehlt, gilt
    der Mittelwert wie bis 344. Der Satz nennt die schlechteste Kamera und die Regel."""
    from . import belichtung as _belichtung  # noqa: PLC0415
    werte = []
    for eintrag in je_kamera or ():
        if isinstance(eintrag, dict):
            urteil = eintrag.get("geometrie_urteil") or eintrag.get("stimmung")
            wert = _kontrast_von(urteil)
            if wert is not None:
                werte.append((wert, eintrag.get("kamera"), _umriss_von(urteil)))
    if not werte:
        wert = _kontrast_von(geometrie_urteil)
        if wert is not None:
            werte.append((wert, (geometrie_urteil or {}).get("kamera"),
                          _umriss_von(geometrie_urteil)))
    if not werte:
        return
    kleinster, kamera, umriss = min(werte, key=lambda w: abs(w[0]))
    qa[FELD_KONTRAST] = kleinster
    if umriss is not None:
        qa[FELD_KONTRAST_UMRISS] = umriss
    kaum = [(w, k, u) for w, k, u in werte if _belichtung.haus_kaum_sichtbar(w, u)[0]]
    if not kaum:
        return
    am_umriss = [e for e in kaum if e[2] is not None]
    if am_umriss:
        mittel, kamera, umriss = min(am_umriss, key=lambda w: abs(w[2]))
        hinweise.append(
            f"{SATZ_KAUM_SICHTBAR}: Im Cycles-Bild der Kamera {kamera!r} hebt sich das Haus "
            f"am Umriss nur um {abs(umriss):.1f} Grauwerte vom Hintergrund daneben ab (Haus "
            f"innen gegen Hintergrund aussen, im Betrag; Schwelle "
            f"{_belichtung.KONTRAST_UMRISS_SCHWELLE:.0f}) — es verschwimmt. Stimmung oder "
            f"Hintergrund pruefen. Mittelwert Haus gegen Hintergrund: {mittel:+.1f}.")
        return
    mittel, kamera, _ = min(kaum, key=lambda w: abs(w[0]))
    hinweise.append(
        f"{SATZ_KAUM_SICHTBAR}: Im Cycles-Bild der Kamera {kamera!r} hebt sich das Haus "
        f"nur um {mittel:+.1f} Grauwerte vom Hintergrund daneben ab (Schwelle "
        f"{_belichtung.KONTRAST_SCHWELLE:.0f}) — es verschwimmt. Stimmung oder "
        f"Hintergrund pruefen. Am Umriss nicht gemessen — es gilt der Mittelwert.")


def _kontrast_ki_eintragen(qa: dict, geometrie_urteil, je_kamera) -> None:
    """``qa.kontrast_haus_hintergrund_ki``: je Kamera am KI-Bild gemessen, für den Lauf der
    kleinste Betrag — gleich gebaut wie :func:`_kontrast_eintragen`, aber ohne Satz."""
    def von(urteil):
        return (_kontrast_von({"kontrast": urteil.get(URTEIL_KONTRAST_KI)})
                if isinstance(urteil, dict) else None)
    werte = [w for w in (von(e.get("geometrie_urteil")) for e in (je_kamera or ())
                         if isinstance(e, dict)) if w is not None]
    if not werte and von(geometrie_urteil) is not None:
        werte = [von(geometrie_urteil)]
    if werte:
        qa[FELD_KONTRAST_KI] = min(werte, key=abs)


#: Neue Baumasse ausserhalb des Umrisses (auf-20261020-294, B6): wieviel das KI-Bild dort
#: baut, wo das Modell Himmel hat, im Verhältnis zur Fläche des Hauses (``aiimaging.baumasse``).
#: Im ``qa``-Block der Lauf mit dem GRÖSSTEN Wert, und je Kamera. Fehlt, wenn nicht gemessen —
#: kein ``null``. Eine Auskunft, kein Tor: ``geometry`` bleibt Feld für Feld, wie es war.
FELD_AUSSERHALB = "ausserhalb_umriss_anteil"
#: Der Satz, wenn das Bildmodell über den Umriss hinaus baut.
SATZ_AUSSERHALB = "KI BAUT UEBER DEN UMRISS HINAUS"


def urteil_fuer_umrisssaetze(urteil):
    """Das Urteil, von dem die Saetze zum Umriss kommen — bei «Umriss halten nachher» das des
    GEHALTENEN Bilds (auf-20261021-303, B1).

    Mit ``vis.umriss_halten: "nachher"`` wird ein anderes Bild geliefert als das, an dem die
    Seedwahl gewaehlt hat. Das Kameraurteil (und damit ``qa.geometry``) bleibt das von vor dem
    Halten; die Saetze «KI BAUT UEBER DEN UMRISS HINAUS» und «HAUS IM KI-BILD NICHT
    WIEDERZUERKENNEN» und ``qa.ausserhalb_umriss_anteil`` sagen aber etwas ueber das gelieferte
    Bild — sie lesen darum ``umriss_halten.urteil_nachher`` (``abholer.umriss_halten_der_kamera``).
    Ohne Schalter, bei «im_lauf» oder ohne Nachmessung: das Urteil, wie es ist.
    """
    if not isinstance(urteil, dict):
        return urteil
    uh = urteil.get(URTEIL_UMRISS_HALTEN)
    if (isinstance(uh, dict) and uh.get("angewandt") is True and uh.get("art") == "nachher"
            and isinstance(uh.get("urteil_nachher"), dict) and uh["urteil_nachher"]):
        return dict(urteil, **uh["urteil_nachher"])
    return urteil


#: Welche Zählung von ``baumasse.ausserhalb_umriss`` bei «Umriss halten im Lauf» gilt
#: (auf-20261021-309, B1): ``anteil_haus_nah`` — was so nah wie das Haus ist.
FELD_AUSSERHALB_IM_LAUF = "anteil_haus_nah"


def haelt_im_lauf(urteil) -> bool:
    """Ob am Kameraurteil «Umriss halten» mit Art ``im_lauf`` gerechnet hat."""
    uh = urteil.get(URTEIL_UMRISS_HALTEN) if isinstance(urteil, dict) else None
    return (isinstance(uh, dict) and uh.get("angewandt") is True
            and uh.get("art") == "im_lauf")


def _ausserhalb_von(urteil):
    """Die Baumasse ausserhalb des Umrisses (Vielfaches der Hausfläche) — ``None``, wo nicht
    gemessen.

    **BEI «UMRISS HALTEN IM LAUF» DIE ZÄHLUNG «SO NAH WIE DAS HAUS» (auf-20261021-309, B1):**
    Mit ``im_lauf`` ist ausserhalb des Hauses das festgehaltene Cycles-Bild — dort kann das
    Bildmodell nichts bauen. Die Zählung «nicht Himmel» las den flachen Verlauf dieses
    Hintergrunds bei abend und bedeckt aber als Baumasse (bis 4,53 der Hausfläche, M2-bedeckt
    sSE), und bei 11 von 24 sauberen M2-Bildern stand «KI BAUT UEBER DEN UMRISS HINAUS».
    ``anteil_haus_nah`` zählt nur, was so nah wie das Haus ist, und trennte in 309 richtig
    (höchstens 0,002). Ohne Schalter und bei ``nachher`` bleibt ``anteil_haus``.
    """
    befund = (urteil or {}).get("ausserhalb_umriss") if isinstance(urteil, dict) else None
    feld = FELD_AUSSERHALB_IM_LAUF if haelt_im_lauf(urteil) else "anteil_haus"
    wert = befund.get(feld) if isinstance(befund, dict) else None
    return wert if isinstance(wert, (int, float)) and not isinstance(wert, bool) else None


def _ausserhalb_eintragen(qa: dict, geometrie_urteil, je_kamera, hinweise: list) -> None:
    """``qa.ausserhalb_umriss_anteil``: je Kamera gemessen, für den Lauf der grösste Wert —
    mit Satz, wenn er die (gesetzte) Schwelle erreicht."""
    from . import baumasse as _baumasse  # noqa: PLC0415
    werte = []
    for eintrag in je_kamera or ():
        if isinstance(eintrag, dict):
            wert = _ausserhalb_von(urteil_fuer_umrisssaetze(eintrag.get("geometrie_urteil")))
            if wert is not None:
                werte.append((wert, eintrag.get("kamera")))
    if not werte:
        wert = _ausserhalb_von(urteil_fuer_umrisssaetze(geometrie_urteil))
        if wert is not None:
            werte.append((wert, (geometrie_urteil or {}).get("kamera")))
    if not werte:
        return
    groesster, _kamera = max(werte, key=lambda w: w[0])
    qa[FELD_AUSSERHALB] = groesster
    # JE KAMERA EIN SATZ, WIE BEI «NICHT WIEDERZUERKENNEN» (auf-20261021-314, B6): Bis dahin
    # stand er nur fuer die Kamera mit dem groessten Wert (sSE), obwohl nNW (2,13), nNE (2,25)
    # und sSW (3,33) auch ueber der Schwelle lagen — dort stand nur «NICHT WIEDERZUERKENNEN».
    # Beide Saetze sagen Verschiedenes (mehr gebaut als modelliert / Modell und Bild decken
    # sich kaum) und stehen darum beide, wo beide gelten. Die Zahl im `qa`-Block bleibt der
    # groesste Wert des Laufs.
    for wert, kamera in werte:
        if wert >= _baumasse.SCHWELLE_ANTEIL_HAUS:
            hinweise.append(
                f"{SATZ_AUSSERHALB}: Im KI-Bild der Kamera {kamera!r} steht neben dem Haus, wo "
                f"das Modell Himmel hat, Baumasse im Umfang von {wert * 100:.0f} % der "
                f"Hausflaeche (Satz ab {_baumasse.SCHWELLE_ANTEIL_HAUS * 100:.0f} %, gesetzt, "
                f"nicht gemessen). Das Bild zeigt mehr Gebaeude, als modelliert ist.")


#: DER HAUSANTEIL AN GRUNDLAGE UND KI-BILD (Video-Befund L4-2, 21.10.2026). Die Pruefung
#: meldete «Das Haus fuellt nur 2.9 %» neben einem KI-Bild mit sichtbar grossem Haus: gemessen
#: war nur die Grundlage (``anteil_soll``), die KI hatte den Ausschnitt naeher erfunden. Jetzt
#: stehen beide Zahlen im ``qa``-Block (Lauf: die Kamera von ``qa.geometry``) und je Kamera,
#: 0..1. Fehlen, wenn nicht gemessen — kein ``null``. Auskunft, kein Tor.
FELD_HAUS_GRUNDLAGE = "haus_anteil_grundlage"
FELD_HAUS_BILD = "haus_anteil_bild"
#: Der Satz, wenn die KI das Haus deutlich anders rahmt als die Grundlage.
SATZ_RAHMT_ANDERS = "KI-BILD RAHMT ANDERS"


def hausanteil_des_urteils(urteil) -> tuple:
    """``(grundlage, bild)`` eines Kameraurteils, je ``None``, wo nicht gemessen.

    ``grundlage`` ist der Hausanteil der Bauwerksmaske (``haus_im_bild.anteil_grundlage`` mit
    ``grundlage_aus: bauwerksmaske``, ohne Platte und Bestand, seit auf-20261021-312), sonst
    ``anteil_soll`` (gezaehlt an der Blender-Tiefe, mit Platte, dieselbe Zahl wie in
    «Das Haus fuellt …»), ``bild`` ``haus_im_bild.anteil`` des GELIEFERTEN Bilds
    (:func:`urteil_fuer_umrisssaetze`). Bei randloser Soll-Silhouette (Innenansicht) beide
    ``None``: Dort ist jeder Bildpunkt «Haus», und die Zahl sagte nichts.
    """
    if not isinstance(urteil, dict) or soll_silhouette_randlos(urteil):
        return None, None

    def zahl(w):
        return (round(float(w), 4) if isinstance(w, (int, float)) and not isinstance(w, bool)
                and math.isfinite(w) and 0.0 <= w <= 1.0 else None)

    geliefert = urteil_fuer_umrisssaetze(urteil)
    befund = geliefert.get("haus_im_bild") if isinstance(geliefert, dict) else None
    # DAS HAUS OHNE PLATTE (auf-20261021-312, B2): Mit Bauwerksmaske zaehlt die Grundlage das
    # Haus allein; `anteil_soll` traegt die Platte mit (60 m: 13,4 % statt 11,6 %). Ohne Maske
    # bleibt es `anteil_soll`.
    eigen = urteil.get("haus_im_bild") if isinstance(urteil.get("haus_im_bild"), dict) else {}
    grundlage = (eigen.get("anteil_grundlage") if eigen.get("grundlage_aus") == "bauwerksmaske"
                 else urteil.get("anteil_soll"))
    return (zahl(grundlage),
            zahl(befund.get("anteil")) if isinstance(befund, dict) else None)


def _hausprozent(w: float) -> str:
    return f"{w * 100:.1f} %"


def _hausanteil_eintragen(qa: dict, geometrie_urteil, je_kamera, hinweise: list) -> None:
    """``qa.haus_anteil_grundlage`` und ``qa.haus_anteil_bild`` — mit Satz, wenn die KI das
    Haus deutlich anders rahmt (:func:`baumasse.rahmt_anders`, gesetzt, nicht gemessen)."""
    from . import baumasse as _baumasse  # noqa: PLC0415
    grundlage, bild = hausanteil_des_urteils(geometrie_urteil)
    if grundlage is not None:
        qa[FELD_HAUS_GRUNDLAGE] = grundlage
    if bild is not None:
        qa[FELD_HAUS_BILD] = bild
    urteile = [(e.get("kamera"), e.get("geometrie_urteil")) for e in (je_kamera or ())
               if isinstance(e, dict)]
    if not urteile:
        urteile = [((geometrie_urteil or {}).get("kamera"), geometrie_urteil)]
    for kamera, urteil in urteile:
        g, b = hausanteil_des_urteils(urteil)
        if _baumasse.rahmt_anders(g, b):
            wo = f" der Kamera {kamera!r}" if kamera else ""
            hinweise.append(
                f"{SATZ_RAHMT_ANDERS}: Im KI-Bild{wo} fuellt das Haus geschaetzt "
                f"{_hausprozent(b)}, in der Grundlage {_hausprozent(g)} — die KI hat den Ausschnitt "
                f"{'naeher' if b > g else 'weiter'} gewaehlt als bestellt. Zahlen zur "
                f"Grundlage (Hausanteil, Geometrie) sprechen ueber die Grundlage, nicht ueber "
                f"dieses Bild. Der Wert am KI-Bild ist aus der Tiefe geschaetzt, nicht gezaehlt.")


#: Der Satz, wenn das Haus im KI-Bild nicht wiederzuerkennen ist (auf-20261020-295, N2).
SATZ_NICHT_WIEDERZUERKENNEN = "HAUS IM KI-BILD NICHT WIEDERZUERKENNEN"


def _wiedererkennung_von(urteil):
    """``geom_iou`` eines Kameraurteils — nur, wenn gemessen (nicht randlos, nicht leer)."""
    if not isinstance(urteil, dict) or urteil.get("nur_grundlage"):
        return None
    if soll_silhouette_randlos(urteil) or keine_gemeinsame_silhouette(urteil):
        return None
    wert = urteil.get("geom_iou")
    return wert if isinstance(wert, (int, float)) and not isinstance(wert, bool) else None


def wiedererkennung_des_urteils(urteil) -> dict | None:
    """:func:`umriss.wiedererkennung` für ein Kameraurteil — ``None``, wo nicht gemessen.

    Liest ``geom_iou``, ``n_ist``/``n_soll`` und ``ausserhalb_umriss.anteil_haus`` am Urteil
    (auf-20261021-296, N1). Eine Stelle für Satz und Seedwahl, damit beide dasselbe meinen.
    """
    from . import umriss as _umriss  # noqa: PLC0415
    wert = _wiedererkennung_von(urteil)
    if wert is None:
        return None
    # DIE LANGE BILDSEITE DER MESSUNG (auf-20261021-299): der vierte Ausloeser gilt erst ab
    # 960 px — an 480 px liegt n_ist/n_soll 0,01-0,08 hoeher. Ohne Groesse kein vierter Ausloeser.
    seiten = [urteil.get(k) for k in ("breite", "hoehe")]
    seiten = [v for v in seiten if isinstance(v, (int, float)) and not isinstance(v, bool)]
    return _umriss.wiedererkennung(wert, n_ist=urteil.get("n_ist"), n_soll=urteil.get("n_soll"),
                                   ausserhalb_anteil=_ausserhalb_von(urteil),
                                   lange_seite=max(seiten) if seiten else None)


def _wiedererkennung_eintragen(geometrie_urteil, je_kamera, hinweise: list) -> None:
    """Der Satz «HAUS IM KI-BILD NICHT WIEDERZUERKENNEN» je Kamera unter der Schwelle.

    **Anlass (auf-20261020-295, N2):** «abend voll» zeigte den Blick unter ein Vordach
    (``geom_iou`` 0,005), eine Umriss-IoU aus Farbe meldete trotzdem 0,60. Ein Mass aus
    Farbe und Kanten darf darum nicht «gut» heissen, wenn die Silhouetten sich kaum decken
    (``umriss.umriss_gilt``). Nur ein Satz in ``verdict.hinweise`` — ``qa.geometry`` und
    ``geometry_gates`` bleiben Feld für Feld, wie sie waren.

    **Seit auf-20261021-296 (N1)** auch, wenn das Bild weit mehr «Haus» zeigt, als modelliert
    ist, oder weit über den Umriss baut und die Silhouetten sich zugleich wenig decken
    (:func:`umriss.wiedererkennung`) — das Strassenbild lag bei ``geom_iou`` 0,197.
    """
    from . import umriss as _umriss  # noqa: PLC0415
    werte = []
    for eintrag in je_kamera or ():
        if isinstance(eintrag, dict):
            # Bei «Umriss halten nachher» das gehaltene Bild (auf-20261021-303, B1).
            urteil = urteil_fuer_umrisssaetze(eintrag.get("geometrie_urteil"))
            befund = wiedererkennung_des_urteils(urteil)
            if befund is not None:
                werte.append((befund, eintrag.get("kamera"), urteil))
    if not werte:
        urteil = urteil_fuer_umrisssaetze(geometrie_urteil)
        befund = wiedererkennung_des_urteils(urteil)
        if befund is not None:
            werte.append((befund, (urteil or {}).get("kamera"), urteil))
    for befund, kamera, urteil in werte:
        if befund["gilt"]:
            continue
        wert = float(urteil["geom_iou"])
        n_g, n_s, n_i = urteil.get("n_gemeinsam"), urteil.get("n_soll"), urteil.get("n_ist")
        teile = []
        if _umriss.AUSLOESER_GEOM_IOU in befund["ausloeser"]:
            zaehlung = (f" ({n_g} von {n_s} Punkten des Modells gemeinsam)"
                        if isinstance(n_g, int) and isinstance(n_s, int) else "")
            teile.append(f"decken sich Modell und Bild kaum (geom_iou {wert:.3f}, Schwelle "
                         f"{_umriss.WIEDERERKENNUNG_GEOM_IOU:.1f}){zaehlung}")
        if _umriss.AUSLOESER_FLAECHE in befund["ausloeser"]:
            teile.append(f"zeigt das Bild weit mehr Haus, als modelliert ist ({n_i} Punkte "
                         f"gegen {n_s} im Modell, Verhaeltnis {n_i / n_s:.2f}, Schwelle "
                         f"{_umriss.WIEDERERKENNUNG_FLAECHE_VERHAELTNIS:.1f}, gesetzt, nicht "
                         f"gemessen; geom_iou {wert:.3f})")
        if _umriss.AUSLOESER_AUSSERHALB in befund["ausloeser"]:
            teile.append(f"baut das Bild weit ueber den Umriss hinaus "
                         f"({_ausserhalb_von(urteil):.2f} der Hausflaeche, Schwelle "
                         f"{_umriss.WIEDERERKENNUNG_AUSSERHALB_ANTEIL:.1f}) und deckt das Modell "
                         f"wenig (geom_iou {wert:.3f} unter "
                         f"{_umriss.WIEDERERKENNUNG_GEOM_IOU_BEI_AUSSERHALB:.1f}, beide gesetzt, "
                         f"nicht gemessen)")
        if _umriss.AUSLOESER_VERHAELTNIS_AUSSERHALB in befund["ausloeser"]:
            teile.append(f"zeigt das Bild mehr Haus, als modelliert ist (Verhaeltnis "
                         f"{n_i / n_s:.2f}, Schwelle "
                         f"{_umriss.WIEDERERKENNUNG_VERHAELTNIS_BEI_AUSSERHALB:.1f}), und baut "
                         f"zugleich weit ueber den Umriss ({_ausserhalb_von(urteil):.2f} der "
                         f"Hausflaeche, Schwelle {_umriss.WIEDERERKENNUNG_AUSSERHALB_ANTEIL:.1f}; "
                         f"beide gesetzt an einem Augenurteil, nicht gemessen, gilt ab "
                         f"{_umriss.WIEDERERKENNUNG_MINDEST_LANGE_SEITE} px)")
        hinweise.append(
            f"{SATZ_NICHT_WIEDERZUERKENNEN}: Im KI-Bild der Kamera {kamera!r} "
            f"{'; und '.join(teile)}. Masse aus Farbe und Kanten "
            f"(Umrisstreue, Umriss-IoU) koennen hier gut aussehen und gelten fuer dieses "
            f"Bild nicht.")


#: Die Schluessel der beiden Messschalter am Kameraurteil (Entscheid 117) — dieselben Woerter
#: wie in ``abholer`` (``URTEIL_BILDEINGANG``, ``URTEIL_FARBABGLEICH``).
URTEIL_BILDEINGANG = "bildeingang"
URTEIL_FARBABGLEICH = "farbabgleich"
#: Der Anfang der beiden Saetze in ``verdict.hinweise`` — Proben und Auswerter suchen danach.
SATZ_BILDEINGANG = "BILDEINGANG (Messschalter vis.bildeingang, Entscheid 117)"
SATZ_FARBABGLEICH = "FARBABGLEICH (Messschalter vis.farbabgleich, Entscheid 117)"
#: Der Schluessel des Vermerks «Umriss halten» am Kameraurteil (Strang Treue, 21.10.2026).
URTEIL_UMRISS_HALTEN = "umriss_halten"


#: Der Anfang des Satzes, wenn das KI-Bild ohne das Grundlagenbild entstand (auf-20261021-312
#: B3, 313 B4) — Proben und Auswerter suchen danach.
SATZ_OHNE_GRUNDLAGENBILD = "KI-BILD OHNE GRUNDLAGENBILD"


def modus_satz(kamera, modus, backbone_name=None, *, umriss_im_lauf: bool = False,
               bildeingang_abgeschaltet: bool = False) -> str | None:
    """Der Satz, wenn ein Bild anders gerechnet wurde als bestellt — sonst ``None``.

    **Befund 312/313:** In allen sechs KI-Läufen stand ``angewandt.modus.abweichung: true``
    (bestellt ``image_edit``, gerechnet ``txt2img``), und das Ergebnis lautete trotzdem
    «geliefert» ohne ein Wort dazu. Die Vorgabe ``z-image-turbo`` hat keinen Eingang für das
    Ausgangsbild (``Backbone.bildeingang_traegt=False``, gemessen auf-20260919-123); an die
    Grundlage bindet dann allein die Tiefenkarte. Der Satz sagt, was gerechnet wurde, warum —
    aus dem Register, nicht erfunden — und was trotzdem band. Er bricht nichts ab: Das Bild ist
    ein gültiges Bild, nur nicht das bestellte.

    ``None`` ohne Abweichung, ohne Vermerk oder wenn das Bildmodell nichts gemeldet hat
    (``abweichung`` ``None`` heisst UNBEKANNT, nicht abweichend).

    **Mit «Umriss halten im Lauf»** (``umriss_im_lauf``, auf-20261022-327 B2): Dann kommt das
    Cycles-Bild sehr wohl an — ausserhalb des Hauses, in jedem Schritt in die Latenten gesetzt.
    Der Satz behält seinen Anfang (:data:`SATZ_OHNE_GRUNDLAGENBILD`, die Knotenansicht sucht
    danach) und sagt, dass das Grundlagenbild **im Haus** nicht ankam. Bis dahin hiess es an
    jeder Variante mit M2 «Material, Licht und Ausschnitt malt das Modell frei» — ausserhalb
    des Hauses falsch, und in der Generalprobe las es sich, als fände die Variante ihre
    Grundlage nicht.

    **Mit abgeschaltetem Bildeingang** (``bildeingang_abgeschaltet``, ``vis.bildeingang: false``
    bestellt; Ergebnis auf-20261022-342, h): ``modus.bestellt`` ist dann die Vorgabe des
    Registers (``image_edit``), nicht die Bestellung. Der Satz sagt darum «bestellt
    'vis.bildeingang: false'» und lässt den Hinweis «ein Weg … ist vorbereitet — hier nicht
    gerechnet» weg: Er war abgeschaltet, nicht vergessen. Bis dahin stand im selben Ergebnis
    vorn «der Bildeingang ist abgeschaltet» (§258) und dahinter «bestellt 'image_edit'».
    """
    if not isinstance(modus, dict) or modus.get("abweichung") is not True:
        return None
    bestellt, gerechnet = modus.get("bestellt"), modus.get("gerechnet")
    try:
        eintrag = _backbone.hole(str(backbone_name)) if backbone_name else None
    except _backbone.BackboneError:
        eintrag = None
    grund = getattr(eintrag, "bildeingang_grund", None)
    modell = f" beim Bildmodell {backbone_name!r}" if backbone_name else ""
    wo = ""
    if gerechnet == "txt2img" and umriss_im_lauf:
        wo = " im Haus"
        band = ("ausserhalb des Hauses gilt das Cycles-Bild (Umriss halten im Lauf), im Haus "
                "bindet nur die Tiefenkarte (die Form grob; Material und Licht der Fassade malt "
                "das Modell frei)")
    elif gerechnet == "txt2img":
        band = ("an die Grundlage gebunden hat nur die Tiefenkarte (die Form grob; Material, "
                "Licht und Ausschnitt malt das Modell frei)")
    elif gerechnet == "tiefe_als_bild":
        band = "das Modell hat die Tiefenkarte als Bild bearbeitet, nicht das Grundlagenbild"
    else:
        band = "was stattdessen ins Modell ging, hat es nicht gemeldet"
    weg = ""
    if bildeingang_abgeschaltet:
        bestellt = "vis.bildeingang: false"
    elif eintrag is not None and getattr(eintrag, "bildeingang_weg", None):
        weg = (" Ein Weg, auf dem das Grundlagenbild zusaetzlich zur Tiefe ankommt, ist fuer "
               "dieses Modell vorbereitet (vis.bildeingang, Entscheid 117; seit Entscheid 138 "
               "Vorgabe 0,5 fuer Varianten) — hier nicht gerechnet; warum, steht unter "
               "angewandt.messschalter.bildeingang.")
    return (f"{SATZ_OHNE_GRUNDLAGENBILD}, Kamera {kamera!r}: bestellt {bestellt!r}, gerechnet "
            f"{gerechnet!r} — das Grundlagenbild (Cycles) ist{modell}{wo} NICHT angekommen; "
            f"{band}." + (f" Grund: {grund}" if grund else "") + weg)


def umriss_im_lauf_angewandt(vermerk) -> bool:
    """Hat «Umriss halten im Lauf» an dieser Kamera wirklich gerechnet (Vermerk am Urteil)?"""
    return (isinstance(vermerk, dict) and vermerk.get("angewandt") is True
            and vermerk.get("art") == "im_lauf")


def _modus_eintragen(geometrie_urteil, je_kamera, hinweise: list) -> None:
    """Je Kamera, deren Bild anders gerechnet wurde als bestellt, der Satz aus :func:`modus_satz`.

    Nur, wo kein Messschalter ``vis.bildeingang`` gerechnet hat — dessen Satz
    (:data:`SATZ_BILDEINGANG`) nennt die Abweichung schon. Ohne Abweichung kein Satz.
    """
    for kamera, u in _urteile_je_kamera(geometrie_urteil, je_kamera):
        if isinstance(u.get(URTEIL_BILDEINGANG), dict):
            continue
        modus = u.get("modus")
        satz = (modus.get("satz") if isinstance(modus, dict) else None) or modus_satz(
            kamera, modus, (u.get("engine") or {}).get("name")
            if isinstance(u.get("engine"), dict) else None,
            umriss_im_lauf=umriss_im_lauf_angewandt(u.get(URTEIL_UMRISS_HALTEN)))
        if satz and modus.get("abweichung") is True and satz not in hinweise:
            hinweise.append(satz)


#: Der Anfang des Satzes, wenn die Form des KI-Bilds vom Grundbild abweicht (Ergebnisse 337/339).
SATZ_FORM_WEICHT_AB = "FORM WEICHT VOM GRUNDBILD AB"


def _deckung_eintragen(geometrie_urteil, je_kamera, hinweise: list) -> None:
    """Je Kamera mit Deckungsurteil «Form weicht ab» ein Satz (Ergebnisse 337/339).

    **Anlass:** In 339 malte die Variante ohne Bildeingang ein anderes Haus (Flachdach-Kubus,
    keine Fenster), und das Ergebnis nannte sie «deckungsgleich» — die Zahl stand nur in
    ``qa_je_kamera[].deckung``, das Urteil fiel drüben mit der Schwelle 0,10. Seither ist die
    Schwelle 0,25 (``varianten.DECKUNG_KANTEN_IOU_SCHWELLE``), und der Satz steht im Ergebnis.
    """
    from . import varianten as _varianten  # noqa: PLC0415
    for kamera, u in _urteile_je_kamera(geometrie_urteil, je_kamera):
        d = u.get("deckung")
        if isinstance(d, (int, float)) and not isinstance(d, bool):
            # Je Kamera steht oft nur die Zahl (`qa_je_kamera[].deckung`) — Urteil wie dort.
            d = _varianten.deckung(True, float(d))
        if isinstance(d, dict) and d.get("urteil") == _varianten.FORM_WEICHT_AB:
            satz = (f"{SATZ_FORM_WEICHT_AB}, Kamera {kamera!r}: Kanten des KI-Bilds gegen das "
                    f"Grundbild {d.get('kanten_iou')} unter {d.get('schwelle')} — gleiche "
                    f"Grundlage, aber Form oder Fensterteilung nicht wie im Grundbild "
                    f"(Schwelle {_varianten.DECKUNG_HERKUNFT}).")
            if satz not in hinweise:
                hinweise.append(satz)


def _fenster_eintragen(geometrie_urteil, je_kamera, hinweise: list) -> None:
    """Je Kamera, deren KI-Bild das Glas des Grundbilds verliert, ein Satz (Mac-Befund 23.10.2026).

    **Anlass:** Mappe «haus-am-hang», Bildeingang 0,5, Kamera sSE — die KI malte das
    Fensterband im OG mit Lattung zu, und das Ergebnis meldete «bestanden»: Die Tiefe sieht
    kein Glas, und die Kanten über das ganze Bild verlieren an einem schmalen Band zu wenig.
    Ein Satz nur, wenn gemessen und unter der Schwelle (``varianten.FENSTER_GEHALTEN_SCHWELLE``,
    gesetzt) — nicht gemessen oder gehalten schweigt. ``bestanden`` bleibt, wie es ist.
    """
    from . import varianten as _varianten  # noqa: PLC0415
    for kamera, u in _urteile_je_kamera(geometrie_urteil, je_kamera):
        f = u.get(URTEIL_FENSTER)
        if not (isinstance(f, dict) and f.get("gehalten") is False):
            continue
        satz = (f"{_varianten.SATZ_FENSTER_NICHT_GEHALTEN}, Kamera {kamera!r}: nur "
                f"{float(f.get('anteil') or 0.0):.0%} der Glasflaeche des Grundbilds sind im "
                f"KI-Bild als Glas erhalten (Schwelle {f.get('schwelle'):.0%}, gesetzt, nicht "
                f"geeicht) — die KI hat Fenster uebermalt. Am Bild pruefen; volle Guete statt "
                f"Vorschau und weniger Bildeingang halten mehr vom Grundbild.")
        if satz not in hinweise:
            hinweise.append(satz)


def ergebnis_saetze_der_szene(angewandt) -> list[str]:
    """Saetze aus ``angewandt``, die ins Ergebnis gehoeren (Ergebnis 339, Entscheid 138)."""
    if not isinstance(angewandt, dict):
        return []
    saetze = []
    variante = angewandt.get("variante")
    if isinstance(variante, dict) and isinstance(variante.get("satz"), str) and variante["satz"]:
        saetze.append(variante["satz"])
    # Die Stimmung der Variante (Befund 340) — neben dem Satz des Stoffs, wenn beide gelten.
    stimmung_v = variante.get("stimmung") if isinstance(variante, dict) else None
    if isinstance(stimmung_v, dict) and isinstance(stimmung_v.get("satz"), str) \
            and stimmung_v["satz"] and stimmung_v["satz"] not in saetze:
        saetze.append(stimmung_v["satz"])
    # Die weggelassene Punktwolke (R59) — der Render lief ohne sie, und das soll dastehen.
    weg = angewandt.get("kontext_weggelassen")
    if isinstance(weg, dict) and isinstance(weg.get("satz"), str) and weg["satz"] \
            and weg["satz"] not in saetze:
        saetze.append(weg["satz"])
    bi = ((angewandt.get("messschalter") or {}).get("bildeingang") or {})
    grund = bi.get("grund") if isinstance(bi, dict) else None
    if isinstance(grund, str) and grund.startswith(SATZ_BILDEINGANG_LIZENZ):
        saetze.append(grund if grund.endswith(".") else f"{grund}.")
    # Das freie Bild (Entscheid 149): der Satz steht am Bild, neben FORM/FENSTER, nie statt ihrer.
    frei = angewandt.get("freies_bild")
    if isinstance(frei, dict) and isinstance(frei.get("satz"), str) and frei["satz"] \
            and frei["satz"] not in saetze:
        saetze.append(frei["satz"])
    return saetze


def _urteile_je_kamera(geometrie_urteil, je_kamera) -> list:
    """``[(kamera, urteil)]`` aus ``je_kamera``, sonst aus dem einen Geometrie-Urteil."""
    urteile = []
    for eintrag in je_kamera or ():
        if isinstance(eintrag, dict):
            u = eintrag.get("geometrie_urteil") if isinstance(
                eintrag.get("geometrie_urteil"), dict) else eintrag
            urteile.append((eintrag.get("kamera") or u.get("kamera"), u))
    if not urteile and isinstance(geometrie_urteil, dict):
        urteile.append((geometrie_urteil.get("kamera"), geometrie_urteil))
    return urteile


def bildeingang_herkunft_satz(vermerk: dict) -> str:
    """Das Ende des Satzes :data:`SATZ_BILDEINGANG`: woher die Staerke kommt (Ergebnis 357).

    ``Bestellt.`` fuer eine eigene Staerke; fuer die Vorgabe, welche: Situationsmodell (Entscheid
    149, ergaenzt), Variante (149) oder erstes Bild (138). Ein Vermerk von vor dem 24.10.2026
    (``vorgabe`` ohne ``herkunft``) bleibt bei der alten Fassung.
    """
    if not vermerk.get("vorgabe"):
        return "Bestellt."
    if vermerk.get("herkunft") == HERKUNFT_VORGABE_SITUATION:
        return ("Vorgabe fuer ein Situationsmodell (herkunft vorgabe_situationsmodell, "
                "Entscheid 149, ergaenzt).")
    if vermerk.get("art") == "variante":
        return "Vorgabe fuer Varianten (herkunft vorgabe, Entscheid 149)."
    if vermerk.get("art") == "erstes_bild":
        return "Vorgabe fuer das erste Bild (herkunft vorgabe, Entscheid 138)."
    return "Vorgabe fuer Varianten (Entscheid 138)."


def _messschalter_eintragen(geometrie_urteil, je_kamera, hinweise: list) -> None:
    """Je Kamera ein Satz, DASS ein Messschalter gerechnet hat — und was (auf-20261021-298, B1).

    **Befund 298:** Ueber die Bruecke war nicht zu sehen, dass ``vis.bildeingang`` gerechnet
    hatte: kein ``modus``, keiner der Saetze des Bildmodells. Jetzt steht hier je Kamera, was
    gerechnet wurde (Modus, Staerke, Schritte) bzw. dass das gelieferte Bild farbabgeglichen
    ist. Eine Auskunft, kein Vorbehalt — ``qa.geometry`` und ``geometry_gates`` bleiben, wie
    sie waren. Ohne Schalter kein Satz.
    """
    for kamera, u in _urteile_je_kamera(geometrie_urteil, je_kamera):
        bi = u.get(URTEIL_BILDEINGANG)
        # AUCH DIE VORGABE TRAEGT IHREN SATZ (Ergebnis 357, 24.10.2026): Bis dahin bekam die
        # Vorgabe (Entscheid 138) nur einen Satz, wenn das Grundbild NICHT ankam — die Variante
        # mit 0,7 (S2) stand ohne Satz da, die auf dem Situationsmodell mit 0,5 (S2b) mit Satz
        # und «Bestellt.». Jetzt traegt jedes Bild mit Bildeingang den Satz, mit der Herkunft.
        if isinstance(bi, dict):
            gerechnet = bi.get("modus_gerechnet")
            schritte = (f", {bi['schritte_gerechnet']} von {bi['schritte_bestellt']} Schritten"
                        if isinstance(bi.get("schritte_gerechnet"), int)
                        and isinstance(bi.get("schritte_bestellt"), int) else "")
            if bi.get("modus_abweichung") is True:
                kern = (f"bestellt '{bi.get('modus_bestellt')}', GERECHNET '{gerechnet}' — das "
                        f"Cycles-Bild ist NICHT angekommen")
            elif gerechnet is None:
                kern = ("das Bildmodell hat nicht gemeldet, was es gerechnet hat — UNBEKANNT, "
                        "ob das Cycles-Bild ankam")
            else:
                kern = (f"gerechnet '{gerechnet}' (Weg '{bi.get('weg')}'){schritte} — das "
                        f"Cycles-Bild ging als Start ins Modell, die Tiefe blieb Steuerbild")
            hinweise.append(f"{SATZ_BILDEINGANG}, Kamera {kamera!r}: Staerke "
                            f"{bi.get('staerke')}, {kern}. "
                            + bildeingang_herkunft_satz(bi))
        fa = u.get(URTEIL_FARBABGLEICH)
        if isinstance(fa, dict):
            if fa.get("angewandt") is True:
                hinweise.append(
                    f"{SATZ_FARBABGLEICH}, Kamera {kamera!r}: Geliefert wird das an das "
                    f"Cycles-Bild angeglichene KI-Bild (Streckung {fa.get('streckung')}); "
                    f"geprueft wurde das Bild ohne Abgleich, kein Bildpunkt verschoben "
                    f"(Kanten gleich zu {fa.get('kanten_iou')}). Nie Vorgabe.")
            else:
                hinweise.append(
                    f"{SATZ_FARBABGLEICH}, Kamera {kamera!r}: NICHT angewandt — "
                    f"{fa.get('grund') or 'ohne Grund'}. Geliefert wird das KI-Bild, wie es war.")
        uh = u.get(URTEIL_UMRISS_HALTEN)
        if isinstance(uh, dict):
            from . import umrisshalt as _uh  # noqa: PLC0415
            if uh.get("angewandt") is True:
                messung = ""
                if uh.get("art") == _uh.ART_NACHHER:
                    # Seit auf-20261021-303 (B1): die Saetze zum Umriss gelten dem gehaltenen
                    # Bild; das Urteil von vorher (Seedwahl, qa.geometry) steht hier.
                    gehalten = ("die Saetze zum Umriss gelten dem gelieferten, gehaltenen Bild"
                                if isinstance(uh.get("urteil_nachher"), dict)
                                and uh["urteil_nachher"] else
                                "die Saetze zum Umriss gelten dem Bild VOR dem Halten (nicht "
                                "nachgemessen)")
                    messung = (f"; nach dem Halten geom_iou {uh.get('geom_iou_nachher')} und "
                               f"ueber den Umriss {uh.get('ausserhalb_nachher')}, {gehalten}; "
                               f"vor dem Halten geom_iou {uh.get('geom_iou_vorher')} und ueber "
                               f"den Umriss {uh.get('ausserhalb_vorher')} — daran hat die "
                               f"Seedwahl gewaehlt, und qa.geometry bleibt dieses Urteil")
                hinweise.append(
                    f"{_uh.SATZ}, Kamera {kamera!r}: Art '{uh.get('art')}' — ausserhalb des "
                    f"Hauses (Rand {uh.get('rand_px')} px) gilt das Cycles-Bild{messung}. "
                    + ("Vorgabe fuer Varianten (Entscheid 126)." if uh.get("vorgabe")
                       else "Bestellt."))
                # DER SATZ DES BILDMODELLS (auf-20261021-303, B2) — bei «im_lauf» stand er nur
                # im Befund; jetzt auch hier, Wort fuer Wort, einmal je Wortlaut.
                for satz in uh.get("hinweise") or ():
                    if isinstance(satz, str) and satz and satz not in hinweise:
                        hinweise.append(satz)
            elif not uh.get("vorgabe"):
                # Nur ein BESTELLTER Schalter, der nicht wirkte, bekommt den Satz; die Vorgabe
                # fuer Varianten (Entscheid 126) steht dann nur im Vermerk und unter
                # `angewandt.umriss_halten` — sonst truege jedes Bild ohne Maske einen Vorbehalt.
                hinweise.append(
                    f"{_uh.SATZ}, Kamera {kamera!r}: NICHT angewandt — "
                    f"{uh.get('grund') or 'ohne Grund'}. Geliefert wird das KI-Bild, wie es war.")


def _qa_je_kamera(job_id: str, je_kamera) -> list[dict]:
    """Je Kamera ein ``{kamera, geometry?, style?}`` — in **ihrer** Form.

    **Gebaut, indem diese Funktion sich selbst aufruft.** Die Umrechnung unserer Urteile
    in ihre Blöcke steht in :func:`als_ergebnis` und ist über hundert Zeilen lang; sie
    hier ein zweites Mal zu schreiben hiesse, zwei Fassungen zu haben, die morgen
    auseinanderlaufen. *Der Rückruf garantiert, dass ein QA-Block je Kamera genau
    dasselbe bedeutet wie der QA-Block des Laufs.*

    Das ``verdict`` des Rückrufs wird **weggelassen**: Es trägt den Gesamtgrund des Laufs
    und wäre je Kamera eine Aussage, die niemand gemessen hat.
    """
    aus: list[dict] = []
    for eintrag in je_kamera:
        if not isinstance(eintrag, dict):
            raise SzenenError(f"qa_je_kamera-Eintrag ist kein Wörterbuch: {eintrag!r}")
        name = eintrag.get("kamera")
        if not name:
            raise SzenenError(
                "Ein Eintrag in qa_je_kamera ohne 'kamera'. Ihr Vertrag führt das Feld "
                "als Pflicht je Eintrag, und aus gutem Grund: Ohne den Namen ist nicht "
                "erkennbar, welche Ansicht durchfiel.")
        block = als_ergebnis(job_id, [],
                             geometrie_urteil=eintrag.get("geometrie_urteil"),
                             stil_urteil=eintrag.get("stil_urteil"))["qa"]
        satz = {"kamera": str(name)}
        for feld in ("geometry", "style", FELD_UEBERSTRAHLT, FELD_KONTRAST, FELD_KONTRAST_KI,
                     FELD_KONTRAST_UMRISS, FELD_AUSSERHALB,
                     FELD_HAUS_GRUNDLAGE, FELD_HAUS_BILD):
            if feld in block:
                satz[feld] = block[feld]
        # GEGENPROBE 328 (S8, 22.10.2026): Ohne `verdict` traegt eine Kamera ihr «nicht durchgefallen» nur im
        # Statuswort. Bei einem Urteil `bestanden: None` (z. B. Haus unter 20 % des Bildes, Entscheid 70) stand
        # hier `passed: false` mit — spaeter gesetzt — `status: measured`, und Bildvergleich und Kuratieren
        # lasen «durchgefallen», wo der Grund des Laufs «NICHT BEURTEILBAR» sagt. Gemessen, aber nicht
        # entscheidbar heisst in ihrem Vertrag `not_applicable` (dieselbe Zuordnung wie `tore_in_ihren_worten`).
        geo = satz.get("geometry")
        urteil = eintrag.get("geometrie_urteil")
        if (isinstance(geo, dict) and "status" not in geo and isinstance(urteil, dict)
                and urteil.get("bestanden") is None
                and geo.get("geometry_fidelity") is not None):
            satz["geometry"] = dict(geo, status="not_applicable")
        # Ohne Geometrieurteil («nur Grundlage», auf-20261020-293): die Messung der Stimmung.
        stimmung_messung = eintrag.get("stimmung")
        if isinstance(stimmung_messung, dict) and not eintrag.get("geometrie_urteil"):
            for feld, wert in ((FELD_UEBERSTRAHLT, _ueberstrahlt_von(stimmung_messung)),
                               (FELD_KONTRAST, _kontrast_von(stimmung_messung)),
                               (FELD_KONTRAST_UMRISS, _umriss_von(stimmung_messung))):
                if wert is not None:
                    satz[feld] = wert
        # DIE LIEFERUNG DIESER KAMERA (23.09.2026) — nur, wenn der Aufrufer sie kennt;
        # geprueft in `_lieferung_je_kamera`. Fehlt sie, fehlen die Felder und der
        # Auftrag meldet `lieferstatus: null`, statt eine Lieferung zu erfinden.
        lieferung = _lieferung_je_kamera(eintrag)
        if lieferung is not None:
            satz.update(lieferung)
        # STARTWERT UND GERECHNETE POSE (Nr. 85/68, 20.10.2026) — nur, was der Lauf weiss.
        # Die Pose heisst `pose` und nicht `kamera`: `kamera` ist hier schon der Name.
        if isinstance(eintrag.get("seed"), int) and not isinstance(eintrag.get("seed"), bool):
            satz["seed"] = eintrag["seed"]
        if isinstance(eintrag.get("pose"), dict):
            satz["pose"] = dict(eintrag["pose"])
        # DECKUNG (Video-Befund L4-1, Knoten-Vertrag v0.1.10): Kanten-IoU 0..1 des KI-Bilds gegen
        # das Grundbild. Nur wenn gemessen; das Urteil (Schwelle 0,25 seit 337/339) faellt drueben;
        # der Satz `SATZ_FORM_WEICHT_AB` steht seither auch hier (`_deckung_eintragen`).
        iou = eintrag.get("deckung")
        if isinstance(iou, (int, float)) and not isinstance(iou, bool) and 0.0 <= iou <= 1.0:
            satz["deckung"] = round(float(iou), 4)
        aus.append(satz)
    return aus



# --------------------------------------------------------------------------------------
# Die zwei Tore im Vertragsergebnis — der Befund vom 18.09.2026 an der Naht
# --------------------------------------------------------------------------------------
#
# **Der Anlass** (`docs/R3_WELCHES_MASS_TRENNT_2026-09-18.md`): Die alte Geometriepruefung
# liess elf von zwoelf Muellbildern durch, und dieselben zwoelf bestanden sie auch gegen
# die Tiefenkarte eines voellig anderen Gebaeudes. Nachgerechnet sind es **zwei** Fragen,
# und eine einzige Zahl kann beide nicht beantworten:
#
#     rho_maske   folgt das Bild dem Modell ueberhaupt?      (faellt auf null, wenn nicht)
#     geom_iou    folgt es DIESEM Modell und keinem anderen?  (groesste Luecke: +0.149)
#
# `geometrie_qa.zwei_tore(...)` verbindet sie mit UND und haelt bei jedem Lauf eine
# fremde Geometrie dagegen. Was die Software nach aussen gibt, wusste davon bis heute
# nichts — und ein Befund, der die Naht nicht ueberquert, hat niemanden erreicht.
#
# **Additiv, nie an Stelle des Bestehenden.** Der `qa`-Block bleibt byte-identisch: Die
# Gegenseite hat sich ausdruecklich darauf verlassen, und jede bisher gemessene Zahl
# dieses Projekts haengt an ihm. Der neue Block steht daneben, wie `qa_je_kamera` seit
# dem 11.09.2026 daneben steht.

#: Der Schluessel, unter dem die zwei Tore **neben** dem `qa`-Block stehen.
#:
#: **Nicht abgestimmt.** Dieser Name und alle Felder darunter sind von uns gewaehlt; die
#: Gegenseite kennt sie noch nicht. Siehe :func:`als_zwei_tore_block`.
FELD_ZWEI_TORE = "geometry_gates"

#: Der Schluessel, unter dem ein **Kameraurteil** sein ``geometrie_qa.zwei_tore``-Urteil
#: traegt (gesetzt in ``abholer.verarbeiter``).
#:
#: **Warum am Urteil und nicht als eigener Uebergabewert** (Durchsicht 22.09.2026): Der
#: Block `geometry_gates` war gebaut und auf dem Produktweg nie gefuellt — der Abholer
#: reichte kein ``zwei_tore_urteil`` durch, und beide Quellen (Bruecke und eigene Ablage)
#: haetten dafuer ihre Schreibfunktion aendern muessen. Das Kameraurteil reist schon durch
#: beide — bewacht an der geschriebenen Datei beider Wege in
#: ``tests/test_vertrag_jede_kamera_spricht.py``. Steht der Schluessel da und traegt
#: ``None``, heisst das: diese Kamera wurde NICHT GEMESSEN — und der Block erscheint als
#: solcher, statt still zu fehlen.
URTEIL_ZWEI_TORE = "zwei_tore"

#: Der Schluessel, unter dem ein **Kameraurteil** vermerkt, dass ``interior`` bestellt
#: war — ``{"raum", "art", "bestellt", "standpunkt"}`` oder ``None`` (gesetzt in
#: ``abholer.verarbeiter``). ``standpunkt`` sagt, woher der Standpunkt kam
#: (:data:`INNEN_STANDPUNKT_AUS_RAEUMEN` oder :data:`INNEN_STANDPUNKT_MITGESANDT`); bei
#: ``mitgesandt`` sind ``raum`` und ``art`` ``None`` — nicht von uns gewaehlt. ``None``
#: als ganzer Vermerk heisst: ``interior`` war nicht bestellt.
#:
#: Bis zum 23.09.2026 trugen nur Standpunkte ``aus_raeumen`` den Vermerk, und die kommen
#: bei KEINER echten Bestellung vor: KosmoOrbit sendet ``interior`` immer mit benannten
#: Kameras (auf-91 V1).
#:
#: **Befund der Durchsicht vom 22.09.2026:** Die Innenaufgabe trug Raum und Blickart,
#: und niemand las sie. Im Urteil, im Befund und im Vertragsergebnis stand nicht, dass es
#: eine Innenansicht war — und welcher Raum. Ein Innenbild ohne diesen Satz sieht drueben
#: aus wie ein missratenes Aussenbild. Er steht am Urteil aus demselben Grund wie
#: :data:`URTEIL_ZWEI_TORE`: Das Kameraurteil reist schon durch beide Quellen, ohne dass
#: eine ihre Schreibfunktion aendern muss.
URTEIL_INNENANSICHT = "innenansicht"

#: Woher der Standpunkt einer bestellten Innenansicht kam — der Schluessel ``standpunkt``
#: im :data:`URTEIL_INNENANSICHT`-Vermerk (23.09.2026).
#:
#: ``aus_raeumen``: WIR haben ihn gerechnet (``raumkamera.waehle`` auf den Raeumen der
#: IFC) — nur ohne mitgesandte Kameras. ``mitgesandt``: Er kam als benannte Kamera mit der
#: Bestellung; so sendet KosmoOrbit jede Innenbestellung (auf-91 V1). Den Raum haben wir
#: dann nicht gewaehlt, und ob die Kamera innen steht, prueft diese Seite nicht.
INNEN_STANDPUNKT_AUS_RAEUMEN = "aus_raeumen"
INNEN_STANDPUNKT_MITGESANDT = "mitgesandt"


def innenansicht_satz(vermerk, *, gerendert: bool) -> str:
    """Der Satz fuer ``verdict.hinweise`` zu einem :data:`URTEIL_INNENANSICHT`-Vermerk — oder ``""``.

    **Seit dem 30.09.2026 in ``verdict.hinweise``, nicht mehr in ``verdict.reason``**
    (Owner-Entscheid «Auskunft» auf ihre Frage in der Antwort auf auf-152): ``reason``
    zeigt ihre Kachel mit Warnzeichen, ``hinweise`` ist ihr Vertragsfeld fuer Angaben.
    Bis dahin stand er in ``reason``, weil ein Zusatzfeld in ``qa_je_kamera`` drueben still
    abgestreift wuerde (erg-20260917-49) — ``verdict.hinweise`` ist keines, es steht in
    ihrem Vertrag.

    **Der Satz sagt nur, was stimmt** (Durchsicht 23.09.2026). Bis dahin stand «Das Bild
    zeigt den Raum von innen» auch unter einem Ergebnis ohne Bild — nachgestellt: Auge
    ausserhalb der Szenenbox, ``images: []``, und im Grund daneben «NICHT GERENDERT».
    Jetzt:

    * ``aus_raeumen`` und ``gerendert`` — der Satz vom Raum, denn es gibt ein Bild.
    * ``aus_raeumen`` ohne Bild — nur, dass der Standpunkt gerechnet und nicht gerendert
      wurde.
    * ``mitgesandt`` — dass die Innenansicht bestellt war und die Standpunkte von
      KosmoOrbit stammen. Kein Satz ueber den Raum: Den hat hier niemand gewaehlt.

    Args:
        gerendert: Hat die Kamera dieses Urteils ein Bild? ``als_ergebnis`` liest es am
            ``bild_png`` desselben Urteils.
    """
    if not isinstance(vermerk, dict):
        return ""
    if vermerk.get("standpunkt") == INNEN_STANDPUNKT_MITGESANDT:
        return (f"INNENANSICHT BESTELLT: 'interior' {vermerk.get('bestellt')!r} kam mit "
                f"benannten Kameras; die Standpunkte sind die von KosmoOrbit, einen "
                f"eigenen Innenstandpunkt haben wir nicht gerechnet. Raum: nicht von uns "
                f"gewaehlt.")
    if not gerendert:
        return (f"INNENANSICHT BESTELLT: Standpunkt im Raum {vermerk.get('raum')!r} "
                f"({vermerk.get('art')}) aus 'interior' {vermerk.get('bestellt')!r} "
                f"gerechnet, nicht gerendert — zu diesem Standpunkt gibt es kein Bild.")
    return (f"INNENANSICHT: Standpunkt im Raum {vermerk.get('raum')!r} "
            f"({vermerk.get('art')}), aus 'interior' {vermerk.get('bestellt')!r} aus den "
            f"Raeumen der IFC gerechnet. Das Bild zeigt den Raum von innen, nicht das "
            f"Gebaeude von aussen.")


#: Der Schluessel, unter dem ein **Kameraurteil** vermerkt, dass die Kamera ueber dem Dach
#: steht und trotzdem gerechnet wurde — ``{kamera, kamerahoehe_m, gebaeudehoehe_m, grund}``
#: oder ``None`` (gesetzt in ``abholer.verarbeiter``, nur an gerechneten Kameras).
#:
#: **Owner-Entscheid 67 (01.10.2026), «Rechnen, mit Vorbehalt».** Bis dahin wurde eine
#: solche Kamera vor dem Render abgewiesen; KosmoOrbits Auto-Kamera «Übersicht» (16,3 m
#: bei 6 m Gebaeude) machte damit jeden Auto-Auftrag ``fehlgeschlagen`` (auf-20261001-230).
URTEIL_AUFSICHT = "aufsicht"


def aufsicht_satz(vermerk) -> str:
    """Der Satz fuer ``verdict.hinweise`` zu einem :data:`URTEIL_AUFSICHT`-Vermerk — oder ``""``.

    **In ``hinweise`` und nicht in ``reason``**, aus demselben Grund wie
    :func:`innenansicht_satz` (Owner-Entscheid 30.09.2026): ``reason`` zeigt ihre Kachel
    mit Warnzeichen. Eine Aufsicht ist bestellt, nicht missraten — der Satz ist eine
    Auskunft darueber, welche Regeln NICHT angelegt wurden, kein Vorbehalt gegen das Bild.
    Der Wortlaut ist der des Auftrags zu E67.
    """
    if not isinstance(vermerk, dict) or not vermerk.get("kamera"):
        return ""
    return (f"AUFSICHT: Die Kamera {vermerk['kamera']} steht über dem Dach — gerechnet, "
            f"aber nicht nach den Regeln für Architekturaufnahmen in Augenhöhe beurteilt. "
            f"Die Prüfung gegen die Geometrie gilt für sie weiter.")


#: Der Schluessel, unter dem ein **Kameraurteil** vermerkt, dass es eine **Vogelschau** ist —
#: ``{richtung, hoehe_grad, abstand_m, fuellgrad, satz}`` oder fehlt (gesetzt in
#: ``abholer.verarbeiter``, wenn das Modell ein Situationsmodell ist; 24.10.2026, Ergebnis
#: auf-20261024-354). Kein Vertragsfeld; der Satz geht in ``verdict.hinweise``.
URTEIL_VOGELSCHAU = "vogelschau"


def vogelschau_satz(vermerk) -> str:
    """Der Satz fuer ``verdict.hinweise`` zu einem :data:`URTEIL_VOGELSCHAU`-Vermerk — oder ``""``.

    Eine Auskunft, kein Vorbehalt (wie :func:`aufsicht_satz`): Warum die Auto-Kamera von oben
    schaut, statt in Augenhoehe zu stehen.
    """
    if not isinstance(vermerk, dict) or not isinstance(vermerk.get("satz"), str):
        return ""
    return vermerk["satz"]


#: Der Schluessel, unter dem ein **Kameraurteil** die Hoehe seiner Kamera vermerkt, wenn sie
#: keine Augenhoehe ist — ``{kamera, satz}`` oder ``None`` (gesetzt in ``abholer.verarbeiter``
#: ueber ``abholer.kamerahoehe_vermerk``). **Anlass (Ergebnis auf-20261022-341, c):** Die
#: Warnungen des Kerns zur Hoehe standen nur in ``befund.json``, nicht im Ergebnis.
URTEIL_KAMERAHOEHE = "kamerahoehe_hinweis"

#: Der Anfang des Satzes in ``verdict.hinweise`` — Proben und Auswerter suchen danach.
SATZ_KAMERAHOEHE = "KAMERAHOEHE"


def kamerahoehe_satz(vermerk) -> str:
    """Der Satz fuer ``verdict.hinweise`` zu einem :data:`URTEIL_KAMERAHOEHE`-Vermerk — oder ``""``.

    In ``hinweise`` und nicht in ``reason``, wie :func:`aufsicht_satz`: eine Auskunft ueber den
    Standpunkt, kein Urteil ueber das Bild.
    """
    if not isinstance(vermerk, dict) or not isinstance(vermerk.get("satz"), str):
        return ""
    return vermerk["satz"]


#: Der Schluessel, unter dem ein **Kameraurteil** vermerkt, dass sein Bildauftrag fuer eine
#: Innenkamera angepasst wurde — ``{kamera, bestellt, gerechnet, entfernt, vorsatz, grund}``
#: oder ``None`` (gesetzt in ``abholer.verarbeiter``, siehe ``abholer._bildauftrag_innen``).
#:
#: **Anlass (auf-20261001-230, C19):** Ein Prompt fuer alle Kameras mit «klarer Himmel» gab
#: der Innenkamera ein KI-Bild mit Fassade und Himmel.
URTEIL_BILDAUFTRAG = "bildauftrag_innen"


def bildauftrag_satz(vermerk) -> str:
    """Der Satz fuer ``verdict.hinweise`` zu einem :data:`URTEIL_BILDAUFTRAG`-Vermerk — oder ``""``.

    Eine Auskunft, kein Vorbehalt: Sie sagt, mit welchem Text DIESE Kamera gerechnet
    wurde, weil er nicht der bestellte ist. Ein still geaenderter Auftrag waere ein anderes
    Bild unter demselben Namen.
    """
    if not isinstance(vermerk, dict) or not vermerk.get("kamera"):
        return ""
    # «…» und normaler Leerraum statt repr(): Ein Prompt mit geschuetztem Leerzeichen
    # stand sonst als 'klarer\xa0sky' im Hinweis (auf-20261001-235) — Programmschrift in
    # einem Satz fuer Menschen.
    def _wort(t) -> str:
        return f"«{' '.join(str(t).split())}»"
    weg = ", ".join(_wort(t) for t in vermerk.get("entfernt") or ()) or "nichts"
    return (f"INNENKAMERA {vermerk['kamera']}: Bildauftrag angepasst — "
            f"{_wort(vermerk.get('vorsatz'))} vorangestellt, gestrichen: {weg}. Grund: "
            f"{vermerk.get('grund')}.")


def _aufsicht_saetze(geometrie_urteil, je_kamera) -> list[str]:
    """Die Saetze zu Aufsicht und Innen-Bildauftrag aller Kameras, je Kamera einmal.

    Gelesen wird am Eintrag selbst (dort steht der Vermerk auch ohne Messung) und an
    seinem Urteil; ohne ``je_kamera`` — ein Aufrufer mit nur einem Urteil — am
    ``geometrie_urteil``. Reihenfolge: je Kamera, in der Folge der Kameras.
    """
    quellen = [e for e in (je_kamera or ()) if isinstance(e, dict)]
    if not je_kamera and isinstance(geometrie_urteil, dict):
        quellen = [geometrie_urteil]
    saetze: list[str] = []
    for eintrag in quellen:
        urteil = eintrag.get("geometrie_urteil") or {}
        for schluessel, bilde in ((URTEIL_AUFSICHT, aufsicht_satz),
                                  (URTEIL_BILDAUFTRAG, bildauftrag_satz),
                                  (URTEIL_BESTAND, bestand_satz),
                                  (URTEIL_KAMERAHOEHE, kamerahoehe_satz),
                                  (URTEIL_VOGELSCHAU, vogelschau_satz)):
            satz = bilde(eintrag.get(schluessel) or urteil.get(schluessel))
            if satz and satz not in saetze:
                saetze.append(satz)
        # DIE UMGEBUNG (Entscheid 76): je Auftrag dieselben Saetze — einmal genuegt.
        for satz in kontext_saetze(eintrag.get(URTEIL_KONTEXT)
                                   or urteil.get(URTEIL_KONTEXT)):
            if satz not in saetze:
                saetze.append(satz)
    return saetze

#: Die drei Zustandswoerter, woertlich aus :mod:`aiimaging.gate` uebernommen.
#:
#: **Warum uebernommen und nicht neu erfunden:** `gate.als_kosmovis_verdikt` bringt den
#: dritten Zustand seit dem 26.08.2026 auf genau diesem Weg ueber die Naht — ein
#: Statuswort neben einem dreiwertigen Wahrheitswert. Zwei Vokabulare fuer dieselbe Sache
#: im selben Ergebnis waeren genau die Sorte tote Kante, gegen die dieses Modul gebaut
#: ist: Wer `ok` lesen kann, soll es ueberall lesen koennen.
STATUS_OK = _gate.STATUS_OK
STATUS_FEHLT = _gate.STATUS_FEHLT
STATUS_DEGENERIERT = _gate.STATUS_DEGENERIERT

#: Das vierte Wort, nur fuer ein einzelnes Tor (Sammel-Nachprobe auf-20261001-230): die
#: Zahl gibt es, aber sie MISST hier nichts — ``geom_iou`` bei einer Soll-Silhouette, die
#: das ganze Bild ist (siehe :func:`soll_silhouette_randlos`). Nach aussen ihr
#: ``not_applicable`` (:data:`TOR_STATUS_IHRE`) — ein Wort ihres Vertrags, keine vierte
#: Schreibweise.
STATUS_NICHT_ANWENDBAR = "nicht_anwendbar"


def _tor_felder(tor, praefix: str, gruende: list[str]) -> dict:
    """Ein einzelnes Tor aus :func:`geometrie_qa.zwei_tore` in flache Vertragsfelder.

    Vier Felder je Tor: der Wert, seine Schwelle, sein Status und sein Urteil. Die
    Aufteilung ist dieselbe wie drueben bei `geometry_fidelity` / `geometry_threshold` /
    `geometry_status`, und sie ist der Grund, warum hier nichts verschachtelt wird.

    **Die Statuszuordnung folgt** :func:`aiimaging.gate.als_kosmovis_verdikt` **Wort fuer
    Wort**, damit dasselbe Wort im selben Ergebnis dasselbe heisst:

    * ``fehlt``       — es liegt gar kein Tor vor (unlesbar oder nicht uebergeben).
    * ``degeneriert`` — das Tor liegt vor, **traegt aber keine endliche Zahl**: NICHT
      GEMESSEN.
    * ``ok``          — gemessen.

    **Gemessen heisst: es liegt eine Zahl vor — nicht: ein Feld behauptet es.** Bis zur
    Nachpruefung am 18.09.2026 stand hier allein ``tor["gemessen"] is True``; ein Tor mit
    ``{"gemessen": True, "wert": None}`` lieferte darum ``rho_mask: null`` zusammen mit
    ``rho_mask_status: "ok"`` und ``rho_mask_passed: true`` — eine leere Stelle, als
    gemessen und bestanden ausgewiesen. Genau die Verwechslung, gegen die der ganze
    Befund geschrieben ist, nur eine Ebene tiefer. Geprueft wird darum der **Wert**:
    keine Zahl (``None``, Text, ``bool``, ``NaN``, ``inf``) heisst NICHT GEMESSEN, ganz
    gleich was danebensteht. ``NaN`` und ``inf`` zaehlen mit, weil sie ueberdies kein
    gueltiges JSON sind und drueben schon am Einlesen scheitern wuerden.

    ``…_passed`` ist **fail-closed** und darum immer ein Wahrheitswert: Was ungeprueft
    ist, wird nicht durchgelassen. Unterscheidbar bleibt es am Status — *nicht gemessen
    und durchgefallen sind beides «nicht bestanden», aber nur eines davon ist ein Befund
    ueber das Bild.*
    """
    if not isinstance(tor, dict):
        gruende.append(f"{praefix}_fehlt")
        return {praefix: None, f"{praefix}_threshold": None,
                f"{praefix}_status": STATUS_FEHLT, f"{praefix}_passed": False}

    wert = tor.get("wert")
    # `bool` ist in Python eine Zahl — `True >= 0.10` waere wahr. Dieselbe Ausnahme wie in
    # `geometrie_qa.zwei_tore` bei der Eingangspruefung.
    ist_zahl = (isinstance(wert, (int, float)) and not isinstance(wert, bool)
                and math.isfinite(wert))
    gemessen = tor.get("gemessen") is True and ist_zahl
    bestanden = gemessen and tor.get("bestanden") is True
    # NICHT ANWENDBAR ist etwas anderes als nicht gemessen (auf-20261001-230): Die Zahl lag
    # vor und wurde weggelassen, weil sie hier nichts misst. Nur ohne Wert anerkannt — ein
    # Tor mit Zahl und diesem Vermerk waere ein Widerspruch, und dann gilt die Zahl.
    nicht_anwendbar = not gemessen and bool(tor.get("nicht_anwendbar"))
    if nicht_anwendbar:
        gruende.append(f"{praefix}_nicht_anwendbar")
    elif not gemessen:
        gruende.append(f"{praefix}_nicht_gemessen")
    elif not bestanden:
        gruende.append(f"{praefix}_unter_schwelle")
    return {praefix: wert if ist_zahl else None,
            f"{praefix}_threshold": tor.get("schwelle"),
            f"{praefix}_status": (STATUS_OK if gemessen else STATUS_NICHT_ANWENDBAR
                                  if nicht_anwendbar else STATUS_DEGENERIERT),
            f"{praefix}_passed": bestanden}


def als_zwei_tore_block(urteil) -> dict:
    """Ein Urteil aus :func:`geometrie_qa.zwei_tore` in flache englische Vertragsfelder.

    Args:
        urteil: Die Antwort von ``geometrie_qa.zwei_tore(...)``. Alles andere gilt als
            fehlendes Urteil und wird fail-closed gemeldet, nicht geworfen — eine
            Ausnahme kann jemand fangen und weiterlaufen.

    Returns:
        ``{status, released, passed, separates, counter_check_status, rho_mask*,
        geom_iou*, fail_reasons, reason, warnings}``.

    **Die Feldnamen, und warum diese.** Die Gegenseite liest flache englische Namen —
    `geometry_fidelity`, `geometry_threshold`, `geometry_status`, `style_score`,
    `fail_reasons`, `passed`, `released` (siehe :func:`aiimaging.gate.als_kosmovis_verdikt`
    und ihr Werkzeug `kosmovis_query_qa_verdict`). Hier steht dieselbe Bauform:

    * ``rho_mask`` — die Rangkorrelation ueber der Bauwerksmaske. Der `qa`-Block fuehrt
      schon ``spearman`` fuer die Fassung ueber das **ganze Bild**; ein zweites
      ``spearman`` waere nicht unterscheidbar, und genau diese Verwechslung ist der
      Befund vom 18.09.
    * ``geom_iou`` — **buchstabengleich zum bestehenden** ``qa.geometry.geom_iou``. Es ist
      dieselbe Zahl, und sie hier anders zu nennen hiesse, zwei Namen fuer eine Messung in
      dasselbe Ergebnis zu schreiben.
    * ``released`` / ``passed`` / ``fail_reasons`` / ``…_threshold`` / ``…_status`` —
      woertlich die Namen, die drueben schon gelesen werden.

    **NICHT ABGESTIMMT.** Kein einziger dieser Namen steht in einem Schema der
    Gegenseite; `kosmovis.render-result/v2` kennt die zwei Tore nicht. Die Wahl ist ein
    **Schluss** aus ihrer bestehenden Namensart, keine Angabe von ihnen. Steht es bei
    ihnen anders, ist es hier eine Zeile — und solange nichts abgestimmt ist, ist dieser
    Block fuer sie ein Zusatzfeld, das ihr `zod`-Schema in aller Regel durchlaesst.

    **Drei Zustaende, nicht zwei — und das ist der Kern.** ``zwei_tore`` kennt
    ``bestanden = None``: *nicht entscheidbar*, weil die Gegenprobe gezeigt hat, dass
    diese Messung gar nicht trennt. Das wird hier **nicht** zu ``false``. Ein
    Vertragsfeld, das «nicht entscheidbar» als «durchgefallen» ausliefert, ist genau der
    Fehler, gegen den der ganze Befund geschrieben ist — und die umgekehrte Verwechslung
    («nicht entscheidbar» als «bestanden») hat am 08.09.2026 zwoelfmal als Erfolg
    gegolten. ``passed`` bleibt darum dreiwertig, wie ``passed`` drueben auch, und
    ``status`` traegt das Wort dazu.

    ``released`` ist wie drueben **fail-closed und nie** ``None``: wahr nur, wenn beide
    Tore gemessen sind, beide bestehen **und** die Gegenprobe wirklich getrennt hat.

    **Eine halbe Gegenprobe zaehlt hier nicht als Trennung.** ``zwei_tore`` setzte
    ``trennt = True``, wenn nur **eine** der beiden fremden Zahlen gemessen wurde: Das
    fremde Tor faellt dann durch, weil es nicht gemessen ist, und aus einer fehlenden
    Messung wird eine positive Aussage. Die Bibliothek ist am 18.09.2026 berichtigt
    worden und meldet dort ``trennt = None``.

    **Diese Naht haengt trotzdem nicht daran.** Sie liest ``gegenprobe["tor_*"]
    ["gemessen"]`` selbst, statt ``trennt`` zu glauben — ``separates`` bleibt ``None``
    und ``counter_check_status`` ``fehlt``, solange nicht beide fremden Zahlen vorliegen,
    und zwar auch dann, wenn drinnen wieder etwas anderes stuende. Eine Vertragsnaht, die
    nur wiederholt, was die Bibliothek sagt, prueft nichts.

    **Und eine unlesbare Gegenprobe zaehlt ebenso wenig.** Traegt ihr Urteil keinen
    ``bool``, bleibt ``separates`` ``None`` — nicht ``True``. Geprueft wird auf ``bool``
    und nicht auf Wahrheitswert: Ein ``"ja"`` ist nicht ``True``, aber es ist truthy, und
    ein Zweig, der alles ausser ``True`` als «hat getrennt» liest, gibt genau dann frei,
    wenn er es nicht duerfte.
    """
    gruende: list[str] = []

    if not isinstance(urteil, dict) or "bestanden" not in urteil:
        # Fail-closed wie `gate._lies_urteil`: kein Urteil heisst nicht freigegeben. Aber
        # `passed` ist hier None und nicht False — False waere eine Aussage ueber das
        # Bild, und vorliegen tut nur eine ueber die Messung.
        return {"status": STATUS_FEHLT, "released": False, "passed": None,
                "rho_mask": None, "rho_mask_threshold": None,
                "rho_mask_status": STATUS_FEHLT, "rho_mask_passed": False,
                "geom_iou": None, "geom_iou_threshold": None,
                "geom_iou_status": STATUS_FEHLT, "geom_iou_passed": False,
                "separates": None, "counter_check_status": STATUS_FEHLT,
                "fail_reasons": ["zwei_tore_fehlt"],
                "reason": ("KEIN TORURTEIL: Es liegt keine Antwort von zwei_tore vor. "
                           "'released: false' heisst hier ungeprueft und nicht "
                           "durchgefallen."),
                "warnings": []}

    tor_a = _tor_felder(urteil.get("tor_folgt"), "rho_mask", gruende)
    tor_b = _tor_felder(urteil.get("tor_dieses"), "geom_iou", gruende)

    bestanden = urteil.get("bestanden")
    if bestanden is not None and not isinstance(bestanden, bool):
        # Geprueft wird auf bool, nicht auf Wahrheitswert — ein "nein" waere truthy und
        # kaeme durch. Dieselbe Stelle wie in `gate._lies_urteil`.
        gruende.append("bestanden_kein_wahrheitswert")
        bestanden = False

    warnungen = [str(w) for w in (urteil.get("warnungen") or ())]

    # ── Die Gegenprobe, und was sie wert ist ──────────────────────────────────────────
    gegen = urteil.get("gegenprobe")
    if not isinstance(gegen, dict):
        counter = STATUS_FEHLT
        trennt = None
        gruende.append("gegenprobe_fehlt")
    elif not all(isinstance(gegen.get(f), dict) and gegen[f].get("gemessen") is True
                 for f in ("tor_folgt", "tor_dieses")):
        counter = STATUS_FEHLT
        trennt = None
        gruende.append("gegenprobe_unvollstaendig")
        warnungen.append(
            "GEGENPROBE UNVOLLSTAENDIG: Nur eine der beiden Zahlen gegen die fremde "
            "Geometrie wurde gemessen. Die fremde Seite faellt dann durch, WEIL sie nicht "
            "gemessen ist — das ist keine Trennung. 'separates' bleibt darum leer.")
    elif not isinstance(gegen.get("bestanden"), bool):
        # NACHGEPRUEFT AM 18.09.2026, und es war die einzige fail-OPEN Stelle dieser Naht:
        # Die Abfrage lautete `gegen.get("bestanden") is True`, und alles andere fiel in
        # den Zweig «hat getrennt». Ein `{"bestanden": "ja"}` — also eine Gegenprobe, die
        # BESTANDEN hat und damit gerade NICHT trennt — kam so als `separates: true`,
        # `counter_check_status: "ok"` und `released: true` heraus. Aus einem unlesbaren
        # Urteil wurde eine Freigabe.
        #
        # Geprueft wird darum auf `bool` und nicht auf Wahrheitswert, wie eine Ebene
        # hoeher bei `bestanden` und wie in `gate._lies_urteil`. Kein lesbares Urteil
        # heisst: keine Trennung, nicht «getrennt».
        counter = STATUS_FEHLT
        trennt = None
        gruende.append("gegenprobe_kein_wahrheitswert")
        warnungen.append(
            "GEGENPROBE UNLESBAR: Ihr Urteil ist kein Wahrheitswert. Ob dieselbe Messung "
            "auch gegen eine fremde Geometrie besteht, ist damit ungeklaert — 'separates' "
            "bleibt leer, und freigegeben wird nichts.")
    elif gegen["bestanden"]:
        # Dieselbe Messung sagt dasselbe ueber ein Gebaeude, das es nicht ist. Damit ist
        # nichts gezeigt — und `degeneriert` ist drueben genau dafuer da.
        counter = STATUS_DEGENERIERT
        trennt = False
        gruende.append("gegenprobe_trennt_nicht")
    else:
        counter = STATUS_OK
        trennt = True

    beide_gemessen = (tor_a["rho_mask_status"] == STATUS_OK
                      and tor_b["geom_iou_status"] == STATUS_OK)
    if bestanden is None:
        gruende.append("nicht_entscheidbar")
        status = STATUS_DEGENERIERT
    elif not beide_gemessen:
        status = STATUS_DEGENERIERT
    else:
        status = STATUS_OK

    reason = str(urteil.get("begruendung") or "")
    if counter == STATUS_FEHLT:
        # OHNE GUELTIGE GEGENPROBE gehoert in das Ergebnis und nicht in ein Logbuch: Wer
        # die Datei liest, muss sehen, dass nicht gegengeprueft wurde. `warnings` traegt
        # den langen Satz, `reason` den kurzen — denn `reason` ist die eine Zeile, die
        # eine Oberflaeche anzeigt.
        #
        # NUR bei `fehlt`. Eine Gegenprobe, die gelaufen ist und NICHT getrennt hat, ist
        # `degeneriert` — dort steht der Satz schon in der Begruendung, und ein zweiter
        # daneben behauptete, sie sei ausgeblieben.
        reason = (reason + " OHNE GUELTIGE GEGENPROBE gegen fremde Geometrie — das "
                           "Urteil ist damit so viel wert wie das alte.").strip()

    # Die Reihenfolge ist die des Lesens: erst das Urteil, dann die Gegenprobe, dann die
    # zwei Zahlen, auf denen beides ruht.
    block = {
        "status": status,
        "released": bool(status == STATUS_OK and bestanden is True and trennt is True),
        # Dreiwertig: None heisst NICHT ENTSCHEIDBAR, nicht durchgefallen.
        "passed": bestanden,
        "separates": trennt,
        "counter_check_status": counter,
    }
    block.update(tor_a)
    block.update(tor_b)
    block.update({"fail_reasons": gruende, "reason": reason, "warnings": warnungen})
    return block

def _pruefe_ein_name_eine_zahl(block: dict, geometrie_urteil) -> None:
    """``geom_iou`` steht zweimal im selben Ergebnis — hier wird geprueft, dass es einmal
    dasselbe heisst.

    :func:`als_zwei_tore_block` nennt die Silhouetten-Ueberdeckung **buchstabengleich** wie
    der bestehende ``qa``-Block, und der Docstring dort sagt warum: *«Es ist dieselbe
    Zahl.»* Nur kamen die beiden bis zur Nachpruefung am 18.09.2026 aus zwei
    Uebergabewerten, die niemand gegeneinander hielt. Ein Ergebnis mit
    ``qa.geometry.geom_iou = 0.6`` neben ``geometry_gates.geom_iou = 0.96`` war moeglich —
    zwei Zahlen unter einem Namen in einer Datei, und der Leser drueben kann nicht wissen,
    welche gilt.

    Geworfen wird nicht: Das Ergebnis ist bereits geschrieben, und eine Ausnahme hier
    liesse den ganzen Lauf verschwinden statt den Widerspruch. Stattdessen **fail-closed** —
    der Widerspruch steht im Block selbst, und freigegeben wird nichts.
    """
    if not isinstance(geometrie_urteil, dict):
        return
    alt = geometrie_urteil.get("geom_iou")
    neu = block.get("geom_iou")
    for wert in (alt, neu):
        if not (isinstance(wert, (int, float)) and not isinstance(wert, bool)
                and math.isfinite(wert)):
            return          # Fehlt eine der beiden, gibt es nichts zu vergleichen.
    if math.isclose(float(alt), float(neu), rel_tol=1e-9, abs_tol=1e-12):
        return

    block["fail_reasons"] = [*block.get("fail_reasons", ()), "geom_iou_widerspruch"]
    block["warnings"] = [*block.get("warnings", ()),
                         f"ZWEI ZAHLEN UNTER EINEM NAMEN: qa.geometry.geom_iou meldet "
                         f"{float(alt):.4f}, dieser Block {float(neu):.4f}. Beide heissen "
                         f"'geom_iou' und sollen dieselbe Messung sein. Solange sie sich "
                         f"widersprechen, gilt keine von beiden."]
    block["released"] = False


def _grund_verbinden(teile) -> str:
    """Die Teilsaetze fuer ``verdict.reason`` zu EINEM lesbaren Satz verbinden.

    **Anlass (Durchsicht 30.09.2026):** Der Grund eines abgebrochenen Laufs las sich
    drueben so: *«… ein Lauf fehlt.; Geometrie None gegen 0.65»*. Die Teilsaetze sind
    ganze Saetze mit Punkt, verbunden wurde mit ``"; "`` — daraus wurde ein «.;», das in
    ihrer Kachel wie ein Tippfehler aussieht. Wer die Zeile neben einem Warnzeichen liest,
    soll sie lesen koennen und nicht erst entziffern muessen.

    Gestrichen wird darum der EINE Schlusspunkt jedes Teils, dem noch ein Teil folgt. Der
    letzte behaelt seinen Punkt, und ein Auslassungszeichen («...») bleibt eines, weil nur
    ein einzelner Punkt faellt. Am Inhalt aendert sich nichts: Jeder Teil steht weiter da,
    in derselben Reihenfolge — `reason` wird nicht kuerzer, und nie leer, wo es Inhalt
    hatte (ihre Oberflaeche zeigt bei jedem nicht leeren `reason` ein Warnzeichen).
    """
    teile = [str(t) for t in teile]
    verbunden = []
    for i, teil in enumerate(teile):
        if i < len(teile) - 1:
            teil = teil.rstrip()
            if teil.endswith(".") and not teil.endswith(".."):
                teil = teil[:-1]
        verbunden.append(teil)
    return "; ".join(verbunden)


def _gegen_schwelle(schwelle) -> str:
    """Der Vergleichsteil eines Satzes in ``verdict.reason``: «gegen 0.65» — oder, wenn
    keine Schwelle da ist, «ohne Schwelle».

    Ein ``None`` gehoert in ein Zahlenfeld (dort steht es als ``null`` und ist
    Vertrag), aber nicht in einen Satz: *«… gegen None»* liest sich drueben wie ein
    Programmfehler und nicht wie eine fehlende Angabe (Durchsicht 30.09.2026).
    """
    return "ohne Schwelle" if schwelle is None else f"gegen {schwelle}"


def geometrie_satz(fid, schwelle, urteil=None) -> str:
    """«Geometrie 0.0 gegen 0.65» — und, wo die nackte Zahl irrefuehrt, was sie misst.

    **Anlass (Video-Befund L4-2, 21.10.2026):** «Geometrie 0.0 gegen 0.65» stand neben
    «nicht beurteilbar» und einem KI-Bild mit grossem Haus. Nachgerechnet an den Heim-PC-
    Ergebnissen 290, 296, 297 und 298 (Protokoll 74): Jede 0.0 dort ist ein ABGESCHNITTENER
    Wert — die Rangkorrelation hatte das falsche Vorzeichen (+0.22 bis +0.59 bei Disparitaet,
    erwartet negativ), der Score wird dann bei 0 gekappt. Kein Rechenfehler, sondern: Das
    KI-Bild ordnet die Tiefe anders als das Modell — meist, weil es den Ausschnitt veraendert
    hat. Der Satz sagt das jetzt in Worten.

    Zwei Zusaetze, beide nur wo sie zutreffen; der Anfang «Geometrie <zahl> gegen <schwelle>»
    bleibt wortgleich (ihre Oberflaeche und unsere Proben lesen ihn):

    * **nicht anwendbar** (``gesamtwert_anwendbar`` False, unter 20 % Hausanteil): die Zahl
      ist nur Auskunft und kein Urteil (Entscheid 70);
    * **abgeschnitten** (Score 0 bei gemessener Polaritaet und Rangkorrelation mit falschem
      Vorzeichen, oder ohne Ueberdeckung): «KI-Bild weicht von der Geometrie ab».
    """
    satz = f"Geometrie {fid} {_gegen_schwelle(schwelle)}"
    u = urteil if isinstance(urteil, dict) else {}
    zusaetze = []
    if u.get("gesamtwert_anwendbar") is False:
        zusaetze.append("nur Auskunft, nicht anwendbar (das Haus fuellt in der Grundlage "
                        "weniger als 20 %)")
    if isinstance(fid, (int, float)) and not isinstance(fid, bool) and fid == 0:
        zeichen, rho, iou = u.get("polaritaet_zeichen"), u.get("spearman"), u.get("geom_iou")
        if (zeichen in (-1, 1) and isinstance(rho, (int, float))
                and not isinstance(rho, bool) and zeichen * rho <= 0):
            zusaetze.append(
                f"KI-Bild weicht von der Geometrie ab: es ordnet die Tiefe anders als das "
                f"Modell (Rangkorrelation {rho:+.2f}, erwartet "
                f"{'negativ' if zeichen < 0 else 'positiv'}); 0.0 ist der bei null "
                f"abgeschnittene Wert, kein Messfehler")
        elif isinstance(iou, (int, float)) and not isinstance(iou, bool) and iou == 0:
            zusaetze.append("KI-Bild weicht von der Geometrie ab: die Umrisse decken sich "
                            "nicht")
    return satz + "".join(f" — {z}" for z in zusaetze)


def _lage_ohne_urteil(geometrie_urteil: dict) -> str:
    """WARUM ein Geometrieurteil ``bestanden: None`` traegt — der Satz fuer ``reason``.

    Herausgezogen am 22.09.2026 aus :func:`als_ergebnis`, damit derselbe Satz auch fuer
    jede andere Kamera in ``qa_je_kamera`` gilt (siehe :func:`_vorbehalte_je_kamera`).
    Der Wortlaut ist unveraendert.
    """
    if geometrie_urteil.get("nicht_anwendbar") is True:
        # Owner-Entscheid 19.09.2026, seit Entscheid 96 (15.10.2026) auch am Knotenweg: An
        # einem Bild aus einer Skizze wurde von Hand gearbeitet — es folgt ABSICHTLICH nicht
        # dem Modell, und genau das wuerde die Pruefung messen.
        return ("NICHT ANWENDBAR (Handeingriff): Das Bild entstand aus einer Skizze und "
                "folgt absichtlich nicht dem Modell; die Geometriepruefung beantwortet hier "
                "die falsche Frage. 'passed: false' heisst hier nicht durchgefallen, sondern "
                "nicht anwendbar.")
    if geometrie_urteil.get("gesamtwert_anwendbar") is False:
        # Owner-Entscheid 08.10.2026 (Visbox-Entscheid 70): unter 20 % Gebaeudeanteil ist
        # der Gesamtwert nicht anwendbar. `passed` bleibt im fremden Vertrag ein
        # Wahrheitswert — der Satz sagt, dass `false` hier nicht durchgefallen heisst.
        anteil = geometrie_urteil.get("anteil_soll")
        # Eine Stelle nach dem Komma: 0,199 hiess mit {:.0%} «nur 20 % … weniger als 20 %»
        # (HomeStation, auf-20261008-267). Mit Leerzeichen vor «%», wie «20 %» im selben Satz
        # (auf-20261008-268).
        wieviel = (f"nur {anteil * 100:.1f} %" if isinstance(anteil, (int, float))
                   else "weniger")
        return (f"NICHT BEURTEILBAR (Gebaeudeanteil): Das Haus fuellt {wieviel} des "
                f"Bildes, weniger als 20 %; der Gesamtwert ist hier nicht anwendbar. "
                f"'passed: false' heisst hier nicht durchgefallen, sondern nicht "
                f"beurteilbar.")
    if (geometrie_urteil.get("torchance") or {}).get("lage") == "zu_klein":
        return ("NICHT BEURTEILBAR (Rahmung): Das Bauwerk fuellt so wenig Bild, dass "
                "das Tor GEMESSEN nicht bestehen kann. 'passed: false' heisst hier "
                "nicht durchgefallen — eine naehere Kamera behebt es, eine gesenkte "
                "Schwelle nicht.")
    if geometrie_urteil.get("score") is not None and \
            geometrie_urteil.get("paarurteil") is None:
        return ("KEIN MASKENWEG: Der Score liegt vor, aber die Abwesenheitspruefung "
                "ist nicht gelaufen — rho_maske, Kante und Paarurteil fehlen. Der "
                "Score ueber das ganze Bild beantwortet nicht, ob ueberhaupt gebaut "
                "wurde (ein leeres Grundstueck erreichte dort 0.9530). 'passed: "
                "false' heisst hier nicht durchgefallen; es fehlt ein "
                "Material-ID-Pass, und ohne Gelaende in der Szene dazu die Angabe "
                "gelaende_erwartet=false.")
    if (geometrie_urteil.get("paarurteil") or {}).get("zustaendig") is False:
        return ("NICHT ZUSTAENDIG: Hinter dem Umriss steht kein Himmel; das zweite "
                "Mass misst in dieser Szene nichts. 'passed: false' heisst hier nicht "
                "durchgefallen, sondern nicht beantwortbar.")
    return ("NICHT GEMESSEN: Es liegt keine Zahl vor. 'passed: false' heisst hier "
            "nicht durchgefallen, sondern ungeprueft — ein Lauf fehlt.")


def _vorbehalte_je_kamera(je_kamera, gesamt) -> list[str]:
    """Je Kamera mit ``bestanden: None`` der Satz, warum ihr ``passed: false`` kein
    Durchfallen ist.

    Args:
        je_kamera: die Eintraege ``{kamera, geometrie_urteil?}`` wie fuer
            :func:`_qa_je_kamera`. Ein Eintrag ohne Urteil traegt dort nur seinen Namen
            und damit schon die Auskunft *nicht gemessen*; er braucht keinen Satz.
        gesamt: das Gesamturteil, **wenn** es selbst schon seinen Lagesatz traegt — dann
            steht dieselbe Kamera nicht ein zweites Mal da. Sonst ``None``.

    **Durchsicht 22.09.2026, und warum ``passed`` dort nicht ``null`` wird:** Eine
    gemessene Kamera ohne Maskenweg (``bestanden: None``) kam in ``qa_je_kamera`` mit
    ``geometry.passed: false`` an — ohne Vorbehalt, also lesbar als *durchgefallen*.
    ``passed`` ist im fremden Vertrag ein Wahrheitswert (siehe den Abschnitt zur dritten
    Antwort in :func:`als_ergebnis`; nur die Zahlenfelder nehmen seit P-NULLGEOMETRIE
    ``null`` an). Der Gesamtblock loest das mit ``passed: false`` UND einem Satz in
    ``verdict.reason`` — und genau dieser Form folgt der Block je Kamera. Der Satz steht im
    Gesamtgrund, weil ``_qa_je_kamera`` das ``verdict`` je Kamera weglaesst und ein
    Zusatzfeld im Eintrag drueben still abgestreift wuerde.
    """
    schon_genannt = gesamt.get("kamera") if isinstance(gesamt, dict) else None
    saetze: list[str] = []
    for eintrag in je_kamera or ():
        if not isinstance(eintrag, dict):
            continue
        urteil = eintrag.get("geometrie_urteil")
        if not isinstance(urteil, dict) or urteil.get("bestanden") is not None:
            continue
        name = eintrag.get("kamera") or urteil.get("kamera")
        if schon_genannt is not None and name == schon_genannt:
            continue
        saetze.append(f"UNGEPRUEFT bei Kamera {str(name)!r} (qa_je_kamera): "
                      f"{_lage_ohne_urteil(urteil)}")
    return saetze


def _randlose_kameras(geometrie_urteil, je_kamera) -> list[str]:
    """Die Namen der gemessenen Kameras mit randloser Soll-Silhouette, je Bild einmal."""
    urteile = [e.get("geometrie_urteil") for e in (je_kamera or ()) if isinstance(e, dict)]
    if not je_kamera:
        urteile = [geometrie_urteil]
    namen: list[str] = []
    for urteil in urteile:
        if (soll_silhouette_randlos(urteil) and not urteil.get("doppelt_von")
                and str(urteil.get("kamera")) not in namen):
            namen.append(str(urteil.get("kamera")))
    return namen


def soll_silhouette_randlos(urteil) -> bool:
    """Deckt die Soll-Silhouette dieses Kameraurteils das GANZE Bild? Dann misst ``geom_iou`` nichts.

    **Der Anlass (Sammel-Nachprobe auf-20261001-230):** Die Innenkamera meldete
    ``geom_iou`` 1.0 — von innen ist in jedem Bildpunkt Wand, Boden oder Decke, die
    Soll-Silhouette ist das ganze Bild. Dann gilt eine Rechenidentitaet, keine Beobachtung:
    ``|soll ∩ ist| / |soll ∪ ist| = |ist| / |Bild|`` — die Zahl zaehlt, wieviel des Bildes
    der Schaetzer fuer Vordergrund haelt, und ein graues Bild erreicht 1.0. Gemessen schon am
    19.08.2026 an einer Bodenebene bis zum Horizont (auf-20260819-15: «geom_iou exakt
    1.0000»); ``geometrie_qa.geometrie_score`` warnt seitdem («Randlose Silhouette»), aber
    der Vertrag fuehrte die 1.0 weiter als gemessen.

    Gelesen wird ``anteil_soll`` (aus ``geometrie_score``, am Urteil). Fehlt es, ist die
    Antwort ``False`` — nicht feststellbar heisst nicht randlos.
    """
    if not isinstance(urteil, dict):
        return False
    anteil = urteil.get("anteil_soll")
    return (isinstance(anteil, (int, float)) and not isinstance(anteil, bool)
            and math.isfinite(anteil) and anteil >= 1.0)


#: Der Satz zu :func:`soll_silhouette_randlos` — einmal, fuer ``verdict.reason`` und das Tor.
SATZ_GEOM_IOU_RANDLOS = (
    "die Soll-Silhouette deckt das ganze Bild (Innenansicht oder bildfuellende Wand) — eine "
    "Ueberdeckung misst dann nichts, jedes Bild erreichte 1.0. 'geom_iou' ist darum leer; "
    "der Score ruht hier allein auf der Rangkorrelation")


#: Der Grund an ``qa.geometry.geom_iou_grund``, wenn ``geom_iou`` leer ist, weil Soll und Ist
#: keinen Bildpunkt gemeinsam haben (auf-20261020-292, B7).
SATZ_GEOM_IOU_NICHT_GEMESSEN = (
    "nicht gemessen: Soll- und Ist-Silhouette haben keinen Bildpunkt gemeinsam — 0.0 waere "
    "hier keine Messung, sondern ein Platzhalter (Rauschen ergaebe dieselbe Zahl)")


def keine_gemeinsame_silhouette(urteil) -> bool:
    """Ist ``geom_iou`` dieses Kameraurteils eine FEHLENDE MESSUNG und kein Nullwert?

    Ja, wenn Soll- und Ist-Karte keinen einzigen Bildpunkt gemeinsam haben
    (``n_gemeinsam`` 0). ``geometrie_qa.geometrie_score`` sagt dazu selbst: Weisses
    Rauschen und das Bild ergaben dort denselben ``geom_iou`` 0.0 — eine Zahl, die fuer
    Rauschen dasselbe sagt wie fuer das Bild, sagt ueber das Bild nichts. Und
    ``verdict.reason`` nennt diese 0.0 seit Demolauf 14 eine FEHLENDE MESSUNG.

    **Warum hier und nicht nur im Satz** (Durchsicht 22.09.2026): ``geometry_gates``
    fuehrte dieselbe 0.0 als gemessen (``geom_iou_status: ok``), im selben Ergebnis wie
    der Satz, der sie eine fehlende Messung nennt. ``abholer._zwei_tore_dieser_kamera``
    liest diese Funktion und reicht dann ``None`` an Tor B.

    Fehlt die Zaehlung am Urteil, gilt dasselbe bei ``score: None`` und ``geom_iou`` genau
    0: Eine Ueberdeckung von null heisst, dass die Schnittmenge leer ist — und die
    Schnittmenge ist, was ``n_gemeinsam`` zaehlt.
    """
    if not isinstance(urteil, dict):
        return False
    n = urteil.get("n_gemeinsam")
    if isinstance(n, int) and not isinstance(n, bool):
        return n == 0
    iou = urteil.get("geom_iou")
    return (urteil.get("score") is None and isinstance(iou, (int, float))
            and not isinstance(iou, bool) and iou == 0)


def _score_besteht_maske_widerspricht(urteil) -> bool:
    """Besteht der Score, waehrend das Paarurteil des Maskenwegs gemessen durchfaellt?

    Geprueft wird mit ``is True`` / ``is False``: Ein Paarurteil, das nicht gemessen hat
    (``bestanden: None``), widerspricht nicht — es schweigt, und das ist etwas anderes.
    """
    if not isinstance(urteil, dict):
        return False
    paar = urteil.get("paarurteil")
    return (urteil.get("bestanden") is True and isinstance(paar, dict)
            and paar.get("bestanden") is False)


def _widersprueche_je_kamera(je_kamera, gesamt) -> list[str]:
    """Je Kamera, deren Maskenweg dem Score widerspricht, ein Satz fuer ``verdict.reason``.

    Args:
        je_kamera: die Eintraege ``{kamera, geometrie_urteil?}`` wie fuer
            :func:`_qa_je_kamera`. Ein Eintrag ohne Urteil ist *nicht gemessen* und
            widerspricht darum nichts.
        gesamt: das Gesamturteil, **wenn** es selbst schon den langen Satz traegt —
            dann steht dieselbe Kamera nicht ein zweites Mal da. Sonst ``None``.

    **Durchsicht 22.09.2026:** Bis dahin sprach nur die schlechteste Kamera. Siehe den
    Kommentar an der Aufrufstelle in :func:`als_ergebnis`.
    """
    schon_genannt = gesamt.get("kamera") if isinstance(gesamt, dict) else None
    saetze: list[str] = []
    for eintrag in je_kamera or ():
        if not isinstance(eintrag, dict):
            continue
        urteil = eintrag.get("geometrie_urteil")
        if not _score_besteht_maske_widerspricht(urteil):
            continue
        name = eintrag.get("kamera") or urteil.get("kamera")
        if schon_genannt is not None and name == schon_genannt:
            continue
        paar = urteil.get("paarurteil") or {}
        saetze.append(
            f"SCORE BESTEHT, MASKENWEG WIDERSPRICHT bei Kamera {str(name)!r}: Score "
            f"{urteil.get('score')}, rho_maske {paar.get('rho')}. 'passed: true' dieser "
            f"Kamera heisst: der Score besteht — nicht, dass dort ueberhaupt gebaut wurde.")
    return saetze


def _tore_gemessen_durchgefallen(tore) -> bool:
    """Ist mindestens ein Tor dieses Urteils GEMESSEN und nicht bestanden?

    Nicht ``tore["bestanden"] is False``: Das ist auch dann falsch, wenn ein Tor bloss
    nicht gemessen wurde (fail-closed in ``geometrie_qa._tor``). Fuer das Urteil der
    Kamera selbst ist das richtig — hier aber wuerde daraus «eine andere Kamera ist
    durchgefallen», und das waere eine Aussage ueber ein Bild, die niemand gemessen hat.
    """
    if not isinstance(tore, dict):
        return False
    return any(isinstance(t, dict) and t.get("gemessen") is True
               and t.get("bestanden") is False
               for t in (tore.get("tor_folgt"), tore.get("tor_dieses")))


def _andere_kameras_einrechnen(block: dict, je_kamera, eigene) -> None:
    """Den Block `geometry_gates` an die UEBRIGEN Kameras des Auftrags binden.

    Der Block beschreibt die Kamera des `qa`-Blocks — die mit dem schlechtesten Score.
    Das muss nicht die mit den schlechtesten Toren sein: Nachgestellt am 22.09.2026 fiel
    eine Kamera mit Score 0.951 an Tor A (``rho_maske`` −0.018), waehrend die mit Score
    0.70 beide Tore bestand. Ohne diese Funktion stuende ``passed: true`` im Block.

    **Ein Auftrag ist so gut wie sein schwaechstes Bild** — dieselbe Regel wie beim
    Score. Faellt eine andere Kamera GEMESSEN durch, wird ``passed`` ``False`` und
    ``released`` ``False``, mit Grund und Kameranamen. Die Zahlen bleiben die der eigenen
    Kamera, damit ``geom_iou`` weiter dasselbe heisst wie im `qa`-Block.

    Eine Kamera ohne Torurteil zaehlt hier NICHT als durchgefallen: *nicht gemessen* ist
    weder ja noch nein. Und ist die eigene Kamera nicht gemessen, bekommt der Block
    seinen Grund dazu, statt nur «kein Torurteil» zu sagen.

    **Die Zwillingsansicht der eigenen Kamera ist keine andere Kamera** (``doppelt_von``,
    siehe ``abholer._finde_zwilling``): Sie traegt dasselbe Bild und dasselbe Torurteil. Faellt
    die eigene Kamera durch, steht das schon im Block; ein zweites Mal unter anderem Namen
    hiesse, ein Bild als zwei Befunde zu zaehlen. Derselbe Grundsatz gilt seit dem
    22.09.2026 fuer den Zwilling einer ANDEREN Kamera: Er wird mit ihr einmal genannt,
    nicht als zweite Kamera daneben.

    **Satz und Feld sagen dasselbe** (Durchsicht 22.09.2026): Ist die eigene Kamera nicht
    gemessen und faellt zugleich eine andere GEMESSEN durch, steht ``passed: false`` im
    Block — und der Grund darf dann nicht «'passed: null' heisst ungeprueft» sagen. Er
    nennt stattdessen, woher das ``false`` kommt.
    """
    # JE BILD EIN BEFUND, nicht je Kameraname (Befund 22.09.2026). Der Zwilling der
    # EIGENEN Kamera wird oben uebersprungen; der Zwilling einer ANDEREN Kamera stand bis
    # dahin als zweiter Name im Grund («'Uebersicht', 'Gegenueber'») — ein Bild, zwei
    # Befunde. Gezaehlt wird darum nach dem Stamm (`doppelt_von` oder der eigene Name),
    # und genannt wird die Kamera, deren Bild es ist; der Zwilling nur, wenn sein Stamm
    # selbst nicht in der Liste steht.
    je_stamm: dict = {}
    for eintrag in je_kamera or ():
        if not isinstance(eintrag, dict):
            continue
        urteil = eintrag.get("geometrie_urteil")
        if not isinstance(urteil, dict):
            continue
        name = eintrag.get("kamera") or urteil.get("kamera")
        if name == eigene:
            continue
        if eigene is not None and urteil.get("doppelt_von") == eigene:
            continue
        if _tore_gemessen_durchgefallen(urteil.get(URTEIL_ZWEI_TORE)):
            stamm = urteil.get("doppelt_von") or name
            if stamm not in je_stamm or name == stamm:
                je_stamm[stamm] = str(name)
    durchgefallen = list(je_stamm.values())
    genannt = ", ".join(repr(n) for n in durchgefallen)

    if block.get("status") == STATUS_FEHLT:
        block["fail_reasons"] = [*block.get("fail_reasons", ()), "kamera_nicht_gemessen"]
        if durchgefallen:
            schluss = (f"'released: false' heisst fuer diese Kamera ungeprueft; "
                       f"'passed: false' kommt von Kamera {genannt}, die GEMESSEN "
                       f"durchfiel.")
        else:
            schluss = ("'passed: null' und 'released: false' heissen hier ungeprueft, "
                       "nicht durchgefallen.")
        block["reason"] = (
            f"NICHT GEMESSEN: Die Kamera {str(eigene)!r}, auf der das Urteil dieses "
            f"Auftrags ruht, wurde nicht gemessen — es gibt kein rho_maske und kein "
            f"geom_iou. {schluss}")
    if not durchgefallen:
        return
    block["fail_reasons"] = [*block.get("fail_reasons", ()),
                             *(f"kamera_nicht_bestanden:{n}" for n in durchgefallen)]
    block["warnings"] = [*block.get("warnings", ()), (
        f"ANDERE KAMERA FAELLT DURCH: {genannt} "
        f"besteht die zwei Tore nicht. Die Zahlen hier gehoeren zur Kamera "
        f"{str(eigene)!r} (der mit dem schlechtesten Score); der Auftrag ist so gut wie "
        f"sein schwaechstes Bild.")]
    if block.get("passed") is not False:
        block["passed"] = False
    block["released"] = False
    # Der Grund muss mitdrehen: Er begann mit «BESTANDEN — …» der eigenen Kamera, und
    # daneben stuende jetzt `passed: false`. Ein Satz, der dem Feld daneben widerspricht,
    # ist schlechter als keiner.
    block["reason"] = (
        f"NICHT BESTANDEN wegen Kamera {genannt}. "
        f"Kamera {str(eigene)!r}: {block.get('reason', '')}").strip()


#: Die Ebenen, die eine Bestellung verlangen kann (E124, Schritt 1, Owner-Entscheid drüben
#: 29.09.2026). Namen aus unserem Vorschlag im Ergebnisblatt B161 §2 (Blatt -03).
EBENEN_ARTEN = ("schoenbild", "tiefe", "material-id")
EBENEN_ALLE = "alle"


def _lies_passes(wert, maengel: list) -> tuple:
    """``render.passes`` → Tupel aus :data:`EBENEN_ARTEN`. ``None``/``[]`` heisst keine."""
    if wert is None:
        return ()
    if wert == EBENEN_ALLE:
        return EBENEN_ARTEN
    if not isinstance(wert, list) or not all(isinstance(w, str) for w in wert):
        maengel.append(f"'render.passes' ist {wert!r}. Erwartet: eine Liste aus "
                       f"{', '.join(EBENEN_ARTEN)} oder \"{EBENEN_ALLE}\".")
        return ()
    fremd = [w for w in wert if w not in EBENEN_ARTEN]
    if fremd:
        maengel.append(f"'render.passes' nennt {', '.join(map(repr, fremd))} — bekannt sind "
                       f"{', '.join(EBENEN_ARTEN)}. Eine unbekannte Ebene raten wir nicht.")
        return ()
    return tuple(dict.fromkeys(wert))


def _ebenen_mit_lieferung(saetze, ebenen) -> None:
    """Eine bestellte, aber fehlende Ebene macht die Kamera «fehlgeschlagen», mit Grund.

    Ihre Bedingung (c) aus der Antwort auf auf-171: **eine** Auskunft über Lieferung, nicht
    zwei — darum am Kamera-Lieferstatus, den sie schon lesen.
    """
    if not saetze or not ebenen:
        return
    fehlend: dict = {}
    for e in ebenen:
        if not e.get("datei"):
            fehlend.setdefault(e.get("kamera"), []).append(
                f"{e.get('art')} ({e.get('grund') or 'nicht erzeugt'})")
    for satz in saetze:
        luecken = fehlend.get(satz.get("kamera"))
        if not luecken:
            continue
        satz["lieferstatus"] = "fehlgeschlagen"
        zusatz = f"BESTELLTE EBENE FEHLT: {', '.join(luecken)}"
        grund = satz.get("lieferstatus_grund") or ""
        satz["lieferstatus_grund"] = f"{grund}; {zusatz}" if grund else zusatz


def als_ergebnis(job_id: str, bilder, *, geometrie_urteil=None, stil_urteil=None,
                 zeiten=None, uebersprungen: bool = False,
                 nicht_gerendert=(), je_kamera=None,
                 zwei_tore_urteil=None, engine=None, ebenen=None,
                 grundlage=None, guete=None, angewandt=None) -> dict:
    """Unsere QA → ``kosmovis.render-result/v2``.

    **Hier liegt die Entscheidung dieses Moduls.** Der fremde Vertrag trägt für die
    Stil-QA die Vorgaben ``threshold: 0.3`` und ``method: 'dinov3'``. Beide sind für uns
    überholt:

    * Der Boden von **SigLIP 2** liegt bei 0.526 — eine Schwelle von 0.30 lässt jedes
      beliebige Bildpaar durch (`auf-20260818-11`, 4950 Paare). Ein Abzeichen „Stil
      bestanden" gegen 0.30 bedeutet **nichts**.
    * Unser Einbetter ist seit Sitzung 06 SigLIP 2, nicht DINOv3.

    Wir senden darum **immer** unsere Schwelle und unser Verfahren mit. Das ist im
    fremden Schema zulässig — ein gesendetes Feld schlägt dort jeden Vorgabewert — und
    es ist die einzige Form, in der ihr Abzeichen etwas aussagt.

    Zusätzlich wandert in ``verdict.reason`` ein Satz darüber, **wogegen** geprüft wurde.
    Wer in der fremden Oberfläche ein rotes Abzeichen sieht, soll nicht erst bei uns
    nachfragen müssen, was die Schwelle war.

    Args:
        job_id: Auftragskennung. Wird gegen ihre Form geprüft (siehe
            :func:`pruefe_job_id`) — die Prüfung meldet, sie wirft nicht.
        bilder: Liste von Bildpfaden.
        geometrie_urteil: Antwort von ``geometrie_qa.geometrie_gate(...)`` oder ``None``.
        stil_urteil: Antwort von ``stil_qa.stil_gate(...)`` oder ``None``.
        zwei_tore_urteil: Antwort von ``geometrie_qa.zwei_tore(...)`` oder ``None``.
            Wandert **neben** den ``qa``-Block, siehe :func:`als_zwei_tore_block`. Ohne
            Angabe fehlt das Feld ganz — ein leerer Block hiesse «gemessen, Ergebnis
            leer», und das ist etwas anderes als «nicht gemessen». **Ausser** das
            ``geometrie_urteil`` traegt den Schluessel :data:`URTEIL_ZWEI_TORE` (so auf dem
            Produktweg seit dem 22.09.2026): Dann kommt das Urteil von dort, und ein
            ``None`` darin erscheint als Block mit ``status: fehlt`` und Grund.
        zeiten: ``{name: sekunden}``, wandert unverändert in ``timings``.
        uebersprungen: Der Auftrag trug ``skip: true`` und wurde **nicht gerechnet**.
        nicht_gerendert: Kurzgründe für Kameras, die **absichtlich** kein Bild bekamen —
            Rahmung, Kamerahöhe, doppelte Ansicht.

            **Warum das ein eigenes Feld braucht** (gemessen am 26.08.2026 über die
            wirkliche Kette): Ein Auftrag, bei dem jede Kamera vom Rahmungsriegel
            abgelehnt wurde, kam mit ``verdict.reason = "NICHT GEMESSEN … ein Lauf
            fehlt"`` zurück. Unsere eigene Befunddatei sagte präzise *«NICHT GERENDERT
            (Rahmung): s, sSE, nNW — das Bauwerk füllt 28 % der Bildbreite»*, und die
            andere Seite bekam davon **nichts**.

            *Absichtlich verweigert und abgestürzt sahen im Vertrag gleich aus.* Genau
            dieselbe Lücke wie bei ``uebersprungen``, eine Ebene tiefer.
            Die **vierte** Lage neben *gemessen*, *nicht gemessen* und *nicht zuständig*
            — und die einzige, die niemand beheben muss. Sie steht hier, weil
            ``passed: false`` ohne diesen Satz aussieht wie ein durchgefallenes Bild;
            in Wahrheit hat der Betreiber selbst abbestellt (Owner-Vertragslücke,
            `auf-vis-20260825-15` Posten 2, angeschlossen am 26.08.2026).

        je_kamera: Je Kamera ``{kamera, geometrie_urteil?, stil_urteil?}`` und — seit
            dem 23.09.2026 — die vier Felder :data:`FELDER_LIEFERUNG`. Sie wandern
            geprueft nach ``qa_je_kamera[]`` (siehe :func:`_lieferung_je_kamera`).
        guete: ``'vorschau'`` oder ``'voll'``, wenn der Auftrag ``vis.guete`` trug
            (Entscheid 104) — dann steht es oben als ``guete``, und bei der Vorschau
            beginnt ``verdict.reason`` mit «VORSCHAU». ``None``: Feld fehlt im Ergebnis
            (rückwärtsverträglich).

    Returns:
        Ein Wörterbuch nach ``kosmovis.render-result/v2``, plus ein Feld ``hinweise``,
        das **nicht** Teil ihres Vertrags ist. Wer strikt gegen ihr Schema prüft, nimmt
        :func:`nur_vertragsfelder`.

        ``lieferstatus`` und ``lieferstatus_grund`` stehen **immer** darin (23.09.2026):
        ``geliefert`` nur, wenn jede Kamera geliefert hat, ``None`` wenn es nicht
        festzustellen ist — siehe :func:`_lieferstatus_des_auftrags`.
    """
    hinweise: list[str] = []
    qa: dict = {}

    kennung = pruefe_job_id(job_id)
    if not kennung["passt"]:
        hinweise.append(kennung["begruendung"])

    if geometrie_urteil is not None:
        qa["geometry"] = {
            "geometry_fidelity": geometrie_urteil.get("score"),
            "spearman": geometrie_urteil.get("spearman"),
            # LEER, WENN DIE SOLL-SILHOUETTE DAS GANZE BILD IST (auf-20261001-230): Dann
            # stuende hier 1.0 fuer jedes Bild — siehe `soll_silhouette_randlos`.
            # UND LEER OHNE GEMEINSAME SILHOUETTE (auf-20261020-292, Befund B7): Dann ist
            # 0.0 eine fehlende Messung, kein Wert — Tor B fuehrt sie seit dem 22.09.2026
            # schon so (`abholer._zwei_tore_dieser_kamera`), der `qa`-Block meldete bis
            # dahin trotzdem 0.0. Der Grund steht in `geom_iou_grund`.
            "geom_iou": (None if (soll_silhouette_randlos(geometrie_urteil)
                                  or keine_gemeinsame_silhouette(geometrie_urteil))
                         else geometrie_urteil.get("geom_iou")),
            "threshold": geometrie_urteil.get("schwelle", geometrie_qa.SCHWELLE_GEOMETRIE),
            "passed": bool(geometrie_urteil.get("bestanden")),
            # DAS VERFAHREN, DAS WIRKLICH LIEF — nicht die Konstante.
            #
            # Bis zum 26.08.2026 stand hier fest `geometrie_qa.METHODE`. Das ist die
            # ungerichtete Fassung (v1, `abs(spearman)`), und sie ist NICHT die, die
            # läuft, wenn der Maskenweg die gemessene Polarität anwenden konnte. Der
            # Vertrag nannte also ein Verfahren, das er nicht kannte.
            #
            # **Der Unterschied ist kein Etikett** (HomeStation, 26.08.): Unter v1
            # besteht ein Bild mit VERTAUSCHTER Tiefe das Tor — durchgerechnet gibt
            # spearman = +0,675 dort 0,6802 statt 0,0000. Wer am `method`-Feld ablesen
            # will, ob die Richtung geprüft wurde, muss das Feld auch lesen können.
            "method": geometrie_urteil.get("methode") or geometrie_qa.METHODE,
        }
        if soll_silhouette_randlos(geometrie_urteil):
            qa["geometry"]["geom_iou_grund"] = f"nicht anwendbar: {SATZ_GEOM_IOU_RANDLOS}"
        elif keine_gemeinsame_silhouette(geometrie_urteil):
            qa["geometry"]["geom_iou_grund"] = SATZ_GEOM_IOU_NICHT_GEMESSEN
        # UND OB DIE RICHTUNG UEBERHAUPT GEPRUEFT WURDE.
        #
        # `rho_maske is None` heisst: Der Maskenweg lief nicht, die gemessene Polarität
        # wurde nicht angewandt, und der Score ist im geometrischen Fehler NICHT MONOTON.
        # Das gehört zum Abzeichen, nicht in eine Datei auf unserer Seite.
        if geometrie_urteil.get("rho_maske") is None and qa["geometry"]["passed"]:
            hinweise.append(
                "RICHTUNG NICHT GEPRUEFT: Der Maskenweg lief nicht (rho_maske fehlt), "
                "darum wurde die gemessene Polaritaet des Tiefenschaetzers nicht "
                "angewandt und der Score mit abs(spearman) gebildet. In diesem Modus ist "
                "er im geometrischen Fehler NICHT MONOTON: Ein Bild mit vertauschter "
                "Tiefe erreicht denselben Wert wie eines mit richtiger. 'passed: true' "
                "sagt hier also nichts darueber, ob die Tiefe richtig herum steht.")
        # Wir werfen dem fremden Vertrag vor, seine Stil-Schwelle sei kein Gate. Es wäre
        # unredlich, dabei zu verschweigen, was wir über die EIGENE gemessen haben.
        if (geometrie_urteil.get("nullanker") is None
                and geometrie_urteil.get("nicht_anwendbar") is not True):
            hinweise.append(
                f"Zur Geometrie-Schwelle {geometrie_qa.SCHWELLE_GEOMETRIE}: Für diesen "
                f"Lauf liegt KEINE Nullprobe vor. Am 20.08.2026 gemessen "
                f"(auf-20260820-21): Auf einer Szene mit viel Boden erreicht weisses "
                f"Rauschen {geometrie_qa.NULLANKER['platte_endlich']['rauschen']}, besteht "
                f"das Gate also — und auf einer Szene mit wenig Boden erreicht selbst ein "
                f"perfektes Bild nur 0.64, kann es also nicht bestehen. Ein grünes "
                f"Abzeichen ist damit zurzeit KEIN Beleg für Geometrietreue. Der Wert ist "
                f"nicht wertlos, er ist noch nicht kalibriert."
            )

    if stil_urteil is not None:
        einbetter = stil_urteil.get("einbetter_name") or "unbekannt"
        aus_belichtung = stil_urteil.get("verfahren") == "belichtungsrahmen"

        if aus_belichtung:
            # Seit dem Owner-Entscheid vom 21.08.2026 ist der Hausstil FEST FORMULIERT und
            # wird gegen einen gemessenen Belichtungsrahmen geprüft, nicht gegen ein
            # Referenzset. Damit beantworten wir ihre Frage — *sieht das aus wie gewollt?*
            # — mit einem anderen Mittel als ihrem.
            #
            # `style_score` bleibt darum LEER. Eine Belichtungsprüfung hat keinen
            # natürlichen Skalar; eine Zahl hineinzuschreiben wäre erfunden, und sie sähe
            # in ihrer Oberfläche genau wie eine Bildähnlichkeit aus. Dasselbe gilt für
            # `threshold`: Ein Rahmen ist kein Schwellwert, sondern ein Intervall je Feld.
            #
            # OFFENE FRAGE AN DIE GEGENSEITE (Übergabeblatt): Nimmt ihr Schema `null` für
            # `style_score` an? Ihre Schemadatei liegt uns nicht vor. Wenn nicht, kommt der
            # Fehler erst in ihrer Warteschlange — und dann ist das dort zu ändern und
            # nicht hier durch eine erfundene Zahl.
            gemessen = bool(stil_urteil.get("gemessen"))
            qa["style"] = {
                "style_score": None,
                "threshold": None,
                "passed": bool(stil_urteil.get("bestanden")) if gemessen else False,
                "method": einbetter,
            }
            if gemessen:
                hinweise.append(
                    f"Stil gegen den BELICHTUNGSRAHMEN geprüft ({einbetter!r}), nicht "
                    f"gegen ein Referenzset — der Hausstil ist seit 21.08.2026 fest "
                    f"formuliert. 'style_score' ist darum leer und nicht 0: Eine "
                    f"Belichtungsprüfung hat keinen Skalar, und einen zu erfinden hiesse, "
                    f"in ihrer Oberfläche eine Bildähnlichkeit vorzutäuschen.")
            else:
                hinweise.append(
                    f"Stil NICHT GEMESSEN: {stil_urteil.get('grund', 'ohne Angabe')} "
                    f"'passed: false' heisst hier ungeprüft und nicht durchgefallen.")
        else:
            schwelle = stil_urteil.get("schwelle", stil_qa.SCHWELLE_STIL)
            qa["style"] = {
                "style_score": stil_urteil.get("score"),
                # NICHT ihre 0.3 — siehe Docstring.
                "threshold": schwelle,
                "passed": bool(stil_urteil.get("bestanden")),
                "method": einbetter,
            }
            hinweise.append(
                f"Stil-Schwelle {schwelle:.3f} statt der fremden Vorgabe 0.30, Verfahren "
                f"{einbetter!r} statt 'dinov3'. Grund: Der Boden von SigLIP 2 liegt bei "
                f"0.526 — gegen 0.30 besteht jedes beliebige Bildpaar (auf-20260818-11)."
            )

    geo_ok = qa.get("geometry", {}).get("passed")
    stil_ok = qa.get("style", {}).get("passed")
    messbar = [x for x in (geo_ok, stil_ok) if x is not None]
    bestanden = bool(messbar) and all(messbar)

    teile = []
    if qa.get("geometry"):
        # Fehlt die Zahl, sagt der Satz es in Worten — «Geometrie None gegen 0.65» las
        # sich drueben wie ein Programmfehler (Durchsicht 30.09.2026). Die Schwelle
        # bleibt genannt, weil sie auch ohne Zahl sagt, WOGEGEN geprueft worden waere.
        # «Geometrie-SCORE nicht gemessen» und nicht «Geometrie nicht gemessen»: Ohne
        # gemeinsame Silhouette fehlt der Score, der Maskenweg kann aber gemessen haben
        # (siehe «KEIN SCORE, ABER MASKENWEG» unten) — der Satz darf ihm nicht
        # widersprechen.
        _fid = qa["geometry"]["geometry_fidelity"]
        _schw = qa["geometry"]["threshold"]
        if _fid is None:
            teile.append("Geometrie-Score nicht gemessen"
                         + (f" (Schwelle {_schw})" if _schw is not None else ""))
        else:
            teile.append(geometrie_satz(_fid, _schw, geometrie_urteil))
    if qa.get("style"):
        if qa["style"]["style_score"] is None:
            # Kein Skalar, also auch kein "x gegen y" — der Satz muss sagen, WOMIT
            # geprüft wurde, sonst liest sich ein leeres Feld wie ein Fehler.
            teile.append(f"Stil gegen den Belichtungsrahmen ({qa['style']['method']}), "
                         f"ohne Ähnlichkeitszahl")
        else:
            teile.append(f"Stil {qa['style']['style_score']} "
                         f"{_gegen_schwelle(qa['style']['threshold'])} "
                         f"({qa['style']['method']})")
    # ── Die dritte Antwort an der Vertragsgrenze ──────────────────────────────────────
    #
    # `passed` ist im fremden Vertrag ein Wahrheitswert und kann kein Drittes tragen. Ein
    # `bestanden: None` unserer Seite wird darum unweigerlich zu `passed: false` — und
    # sieht dort aus wie ein durchgefallenes Bild.
    #
    # Seit P-NULLGEOMETRIE nehmen die ZAHLENFELDER null an (KosmoOrbit, 24.08.2026). Die
    # Zahlen stehen also schon richtig auf null. Was fehlte, war der Satz daneben: WARUM
    # keine Zahl da steht. `reason` ist ein Vertragsfeld und ueberlebt
    # `nur_vertragsfelder` — ein eigenes Statusfeld taete das nicht.
    #
    # Die drei Lagen verlangen verschiedene Handgriffe, und genau darum muessen sie
    # unterscheidbar sein:
    #   nicht gemessen  -> einen Lauf nachholen
    #   nicht zustaendig -> andere Szene oder anderer Schaetzer
    #   Rahmung zu weit  -> naeher heranfahren
    lage = None
    if qa.get("geometry") and geometrie_urteil.get("bestanden") is None:
        lage = _lage_ohne_urteil(geometrie_urteil)
        teile.insert(0, lage)

    # DAS LOCH, DAS OFFEN BLEIBT — und darum im Vertragsgrund steht.
    #
    # Owner-Entscheid 26.08.2026: Ein durchgefallenes Paarurteil sperrt das Tor (noch)
    # nicht, weil die Paarschwellen provisorisch sind. Sichtbar wird es trotzdem, und
    # zwar HIER — im Vertrag, den die Oberflaeche liest, nicht nur im Kurzbefund am
    # Terminal.
    #
    # Der Satz sagt ausdruecklich, dass 'passed: true' hier WENIGER heisst als sonst.
    # Ohne ihn ist ein solcher Lauf von einem sauberen nicht zu unterscheiden — und
    # gemessen ist der Unterschied gross: Ein verschwundenes Bauwerk kam auf Score 0.951
    # bei rho_maske -0.018.
    #
    # SELBSTLOESCHEND: nur wenn der Score besteht UND das Paarurteil widerspricht.
    _geo = geometrie_urteil or {}
    gesamt_widerspricht = _score_besteht_maske_widerspricht(_geo)
    if gesamt_widerspricht:
        teile.insert(0, (
            "SCORE BESTEHT, MASKENWEG WIDERSPRICHT: Das Tor liest den Score, und der "
            "kann bei viel Boden hoch bleiben, obwohl das Bauwerk fehlt (gemessen: "
            "Score 0.951, geom_iou 1.000, rho_maske -0.018 bei VOLLSTAENDIG "
            "verschwundenem Bauwerk). 'passed: true' heisst hier: der Score besteht — "
            "nicht, dass ueberhaupt gebaut wurde."))

    # DERSELBE WIDERSPRUCH AN JEDER ANDEREN KAMERA — Durchsicht 22.09.2026.
    #
    # Der Satz darueber liest nur `geometrie_urteil`, und das ist auf dem Produktweg das
    # Urteil der SCHLECHTESTEN Kamera. Nachgestellt mit zwei Kameras: Die schlechtere
    # (Score 0.70) bestand sauber, die bessere (Score 0.951, rho_maske -0.018) trug den
    # Widerspruch — und `verdict.reason` lautete «Geometrie 0.7 gegen 0.65», sonst
    # nichts. Die Kamera, deren Bauwerk fehlen kann, kam drueben nicht vor.
    #
    # Der Satz je Kamera gehoert in `verdict.reason` und nicht in einen neuen Schluessel
    # in `qa_je_kamera`: Deren Eintrag ist drueben `z.object({kamera, geometry, style})`,
    # nicht strikt — ein Zusatzfeld wuerde beim Einlesen still abgestreift
    # (erg-20260917-49, render-result.ts 366-393). `reason` ist ein Vertragsfeld.
    saetze = _widersprueche_je_kamera(je_kamera, _geo if gesamt_widerspricht else None)
    # UND DER VORBEHALT JE KAMERA, deren `passed: false` kein Durchfallen ist — siehe
    # `_vorbehalte_je_kamera`. Die Kamera des Gesamtsatzes hat ihren Satz schon (`lage`).
    saetze += _vorbehalte_je_kamera(je_kamera, _geo if lage is not None else None)
    # UND DIE KAMERAS, DEREN geom_iou NICHTS MISST (auf-20261001-230) — ein Vorbehalt an
    # der Zahl, darum in `reason`: Er sagt, warum `geom_iou` leer ist, wo es sonst stuende.
    randlos = _randlose_kameras(geometrie_urteil, je_kamera)
    if randlos:
        saetze.append(f"GEOM_IOU NICHT ANWENDBAR, {', '.join(randlos)}: "
                      f"{SATZ_GEOM_IOU_RANDLOS}")
    if saetze:
        # Hinter den Satz der schlechtesten Kamera, nicht davor: Er ordnet den Auftrag ein.
        stelle = 1 if (gesamt_widerspricht or lage is not None) else 0
        teile[stelle:stelle] = saetze

    # DER UMGEKEHRTE FALL: KEIN SCORE, ABER EIN MASKENWEG — Demolauf 14, 01.09.2026.
    #
    # Ohne gemeinsame Silhouette (`n_gemeinsam` 0) gibt es keinen Score und kein
    # spearman; `qa.geometry` meldet dann `geometry_fidelity: null`, `spearman: null`,
    # `geom_iou: 0.0`, `passed: false`. Die Gegenseite kann daraus NICHT unterscheiden,
    # ob nichts lief oder ob das zweite Tor gemessen und gesperrt hat — und in Lauf 14
    # war es das zweite: drei Kameras, drei gemessene, durchgefallene Paarurteile.
    #
    # Der Satz gehoert in `verdict.reason` und nicht nur in `hinweise`:
    # `nur_vertragsfelder` streicht `hinweise` weg, wer strikt gegen ihr Schema liest,
    # saehe die Auskunft also nie. Dieselbe Luecke wie beim Grund fuer einen nicht
    # gerenderten Lauf.
    #
    # SELBSTLOESCHEND: nur wenn der Score fehlt UND das Paarurteil gemessen hat. Steht
    # ein Score da, traegt er das Urteil und diese Zeile schweigt.
    _paar = (_geo.get("paarurteil") or {})
    if _geo.get("gesamtwert_anwendbar") is False:
        # Der Satz aus `_lage_ohne_urteil` traegt den Fall schon (Entscheid 70); ein
        # zweiter «KEIN SCORE»-Satz sagte dasselbe in anderen Worten.
        pass
    elif _geo.get("score") is None and _paar.get("gemessen") is True \
            and _paar.get("urteilt") is False:
        # SEIT DEM 30.09.2026 URTEILT DER MASKENWEG NICHT (Owner-Entscheid auf auf-175): ρ
        # steht da, aber «durchgefallen» waere ein Urteil aus einer Zahl, die nicht trennt.
        teile.insert(0, (
            f"KEIN SCORE; DER MASKENWEG URTEILT NICHT: Ohne gemeinsame Silhouette gibt es "
            f"keine Tiefenordnung zu vergleichen — 'geom_iou: 0.0' und 'spearman: null' "
            f"sind eine FEHLENDE MESSUNG. rho {_paar.get('rho')} ist nur Auskunft (Schwelle "
            f"nicht geeicht, auf-20260929-175). 'passed: false' heisst hier ungeprueft."))
    elif _geo.get("score") is None and _paar.get("gemessen") is True:
        teile.insert(0, (
            f"KEIN SCORE, ABER MASKENWEG: Ohne gemeinsame Silhouette gibt es keine "
            f"Tiefenordnung zu vergleichen — 'geom_iou: 0.0' und 'spearman: null' sind "
            f"hier eine FEHLENDE MESSUNG und kein Nullwert. Gemessen hat der Maskenweg: "
            f"rho {_paar.get('rho')}, Anteil {_paar.get('anteil')}, Paarurteil "
            f"{'BESTANDEN' if _paar.get('bestanden') else 'DURCHGEFALLEN'}. "
            f"'passed: false' heisst hier durchgefallen und nicht ungeprueft."))

    # Die Zahl, die sagt, worueber das Urteil ueberhaupt spricht. Steht VOR den uebrigen
    # Teilen, weil sie alle anderen einordnet: Ist die Schwelle fuer diese Aufnahme
    # unerreichbar, misst jeder Score die SZENE und nicht das Bild
    # (auf-vis-20260826-16, 26.08.2026).
    erreichbar = (geometrie_urteil or {}).get("erreichbarkeit") or {}
    if erreichbar.get("erreichbar") is False:
        teile.insert(0, (
            f"SCHWELLE FUER DIESE AUFNAHME UNERREICHBAR: hoechstens "
            f"{erreichbar.get('hoechster_score'):.4f} moeglich. Auch ein perfektes Bild "
            f"kaeme nicht durch — 'passed: false' sagt hier etwas ueber die AUFNAHME und "
            f"nichts ueber das Bildmodell."))

    # WARUM kein Bild entstand — vor allem anderen ausser der Abbestellung.
    #
    # Ohne diese Zeilen steht im Vertragsergebnis nur, DASS nichts gemessen wurde. Der
    # Unterschied zwischen «wir haben es abgelehnt, und hier ist die Zahl» und «da ist
    # etwas schiefgegangen» ist für die andere Seite der ganze Informationsgehalt.
    # **Die Richtung gehoert auch in `verdict.reason`, nicht nur in `hinweise`.**
    #
    # `nur_vertragsfelder` streicht `hinweise` weg — es ist kein Feld ihres Vertrags. Wer
    # strikt gegen ihr Schema liest, saehe die Warnung also NIE. Genau dieselbe Luecke wie
    # beim Grund fuer einen nicht gerenderten Lauf, und am selben Tag zum zweiten Mal: Die
    # Auskunft war da und nahm einen Weg, der bei der anderen Seite nicht ankommt.
    # **Nur bei einem BESTANDENEN Bild** — und das ist keine Milde, sondern Arithmetik.
    #
    # Der ungerichtete Score ist der Betrag: ``sqrt(abs(rho) * iou)``. Der gerichtete ist
    # ``sqrt(max(0, polaritaet*rho) * iou)``. Wegen ``max(0, x) <= abs(x)`` ist der
    # ungerichtete Wert eine **Obergrenze** des gerichteten. Ein Lauf, der schon mit der
    # Obergrenze durchfaellt, faellt auch gerichtet durch — die fehlende Richtungspruefung
    # aendert an einem roten Abzeichen also nichts.
    #
    # Bei einem GRUENEN aendert sie alles: Dort verspricht das Abzeichen etwas, das nicht
    # gemessen wurde.
    #
    # `tests/test_dritte_antwort_im_vertrag.py` hat diese Zeile beim ersten Entwurf
    # gefangen — sie stand unter jedem Urteil. Der Satz dort trifft es: *«Wer jedem roten
    # Abzeichen einen Erklaersatz beigibt, hat kein Tor mehr, sondern eine
    # Ausredenmaschine.»*
    if ((geometrie_urteil or {}).get("rho_maske") is None
            and qa.get("geometry", {}).get("passed")):
        teile.append("RICHTUNG NICHT GEPRUEFT (Maskenweg lief nicht, siehe hinweise)")

    for zeile in reversed(tuple(nicht_gerendert or ())):
        teile.insert(0, str(zeile))
        hinweise.append(str(zeile))

    # DIE SKIZZE KAM NICHT AN (Entscheid 96, 15.10.2026) — zuvorderst in `reason`, wie auf
    # der Seite zuvorderst am Bild: Ohne den Satz saehe ein Bild aus Tiefenkarte und Text
    # aus wie eine Bearbeitung der Skizze.
    _skizze = (geometrie_urteil or {}).get(URTEIL_SKIZZE)
    if isinstance(_skizze, dict):
        for satz in reversed([str(h) for h in _skizze.get("hinweise") or ()
                              if str(h).startswith(SKIZZE_NICHT_ANGEKOMMEN_ANFANG)]):
            teile.insert(0, satz)
            hinweise.append(satz)

    if uebersprungen:
        # Vor allen anderen: Wer abbestellt hat, braucht keine Erklaerung darueber, was
        # nicht gemessen wurde. Er braucht die Bestaetigung, dass nichts LIEF.
        grund = ("ABBESTELLT: Der Auftrag trug 'skip: true' und wurde nicht gerechnet. "
                 "'passed: false' heisst hier weder durchgefallen noch ungeprueft — es "
                 "war nichts bestellt. Es ist keine GPU-Zeit angefallen.")
    elif isinstance(geometrie_urteil, dict) and geometrie_urteil.get("nur_grundlage") is True:
        # NUR GRUNDLAGE (Nr. 83/81, 20.10.2026): geliefert ist das Cycles-Bild. Die
        # Geometrie-QA misst, ob ein BILDMODELL dem Modell folgt — ohne Bildmodell gibt es
        # nichts zu messen, und «ein Lauf fehlt» waere eine falsche Aufforderung.
        grund = ("NUR GRUNDLAGE: Geliefert ist das Cycles-Bild, ohne KI-Schritt. "
                 "'passed: false' heisst hier weder durchgefallen noch ungeprueft — die "
                 "Geometrie ist das Modell selbst; gemessen wird erst eine KI-Variante.")
    elif not messbar and nicht_gerendert:
        # Es IST etwas gemessen worden — nur eben vor dem Bild, und mit dem Ergebnis,
        # dass kein Bild entstehen soll. Der Satz «keine QA gelaufen» wäre hier eine
        # Untertreibung, die wie ein Fehler aussieht.
        grund = _grund_verbinden(teile)
    elif not messbar:
        grund = ("Keine QA gelaufen — weder Geometrie noch Stil wurden gemessen. "
                 "'passed: false' heisst hier NICHT durchgefallen, sondern ungeprüft.")
    elif (qa.get("geometry") and geometrie_urteil.get("nullanker") is None
          and geometrie_urteil.get("nicht_anwendbar") is not True):
        # Der Satz muss dort stehen, wo das Abzeichen gelesen wird — nicht nur in einem
        # Übergabeblatt, das niemand aufschlägt, während er auf ein Häkchen sieht.
        teile.append("Geometrie-Schwelle NICHT kalibriert (keine Nullprobe, "
                     "siehe hinweise)")
        grund = _grund_verbinden(teile)
        hinweise.append(grund)
    else:
        grund = _grund_verbinden(teile)

    # DIE INNENANSICHT, wenn `interior` bestellt war (22.09.2026). Nach allen Zweigen
    # oben angehaengt, weil sie keinen davon ersetzt: Sie sagt, WOHER der Standpunkt kam,
    # nicht wie es abgeschnitten hat. Bei `uebersprungen` nicht — abbestellt ist
    # abbestellt, und die Kette liefert dort gar kein Urteil.
    #
    # OB ES EIN BILD GIBT, liest der Satz am `bild_png` DESSELBEN Urteils (Durchsicht
    # 23.09.2026) — bis dahin hiess es auch ohne Bild «Das Bild zeigt den Raum».
    # DIE VORSCHAU SAGT ES ZUERST (Entscheid 104a, 20.10.2026): geprueft wie jedes Bild, aber
    # gerechnet mit weniger — das gehoert vor jede andere Aussage, sonst liest jemand das
    # Abzeichen einer Vorschau wie das eines vollen Bilds.
    if guete == GUETE_VORSCHAU and not uebersprungen:
        grund = vorschau_satz((geometrie_urteil or {}).get(URTEIL_GUETE)) + " " + grund
    _vermerk_urteil = geometrie_urteil or {}
    innen = innenansicht_satz(_vermerk_urteil.get(URTEIL_INNENANSICHT),
                              gerendert=bool(_vermerk_urteil.get("bild_png")))
    qa["verdict"] = {"passed": bestanden, "reason": grund}
    # AUSKUNFT, NICHT VORBEHALT (Owner-Entscheid 30.09.2026, Antwort auf auf-152): Der Satz
    # sagt, woher der Standpunkt kam, nicht was an der Aussage fehlt. In `verdict.reason`
    # trug ihre Kachel bei JEDEM Innenbild ein Warnzeichen — eine Dauerwarnung, die sie
    # ausdruecklich vermeiden. Er steht darum in `verdict.hinweise` (Liste, ihr Vertrag
    # render-result.ts:465), dem Ort, den sie selbst dafuer genannt haben. Bis zum
    # 29.09.2026 stand er in `reason`.
    if innen and not uebersprungen:
        qa["verdict"]["hinweise"] = [innen]
        hinweise.append(innen)
    # DIE AUFSICHT (Owner-Entscheid 67, 01.10.2026) UND DER BILDAUFTRAG EINER INNENKAMERA
    # (auf-20261001-230) — dieselbe Art Auskunft am selben Ort. Je Kamera, nicht nur fuer
    # die schlechteste: Die betroffene ist meist NICHT die Kamera, deren Urteil oben steht,
    # und ihr Satz gehoert trotzdem zum Auftrag.
    if not uebersprungen:
        for satz in _aufsicht_saetze(geometrie_urteil, je_kamera):
            qa["verdict"].setdefault("hinweise", []).append(satz)
            hinweise.append(satz)
        # Entscheid 96: woraus das Bild entstand — Auskunft, kein Vorbehalt.
        for satz in skizze_saetze((geometrie_urteil or {}).get(URTEIL_SKIZZE)):
            qa["verdict"].setdefault("hinweise", []).append(satz)
            hinweise.append(satz)
        # UEBERSTRAHLUNG AM HAUS (auf-20261020-292) — Zahl im `qa`-Block, Satz wie oben.
        vorher = len(hinweise)
        _ueberstrahlt_eintragen(qa, geometrie_urteil, je_kamera, hinweise)
        # KONTRAST HAUS – HINTERGRUND (auf-20261020-293) — gleich gebaut.
        _kontrast_eintragen(qa, geometrie_urteil, je_kamera, hinweise)
        # DERSELBE KONTRAST AM KI-BILD (Ergebnis 334) — nur die Zahl, kein Satz.
        _kontrast_ki_eintragen(qa, geometrie_urteil, je_kamera)
        # NEUE BAUMASSE AUSSERHALB DES UMRISSES (auf-20261020-294, B6) — gleich gebaut.
        _ausserhalb_eintragen(qa, geometrie_urteil, je_kamera, hinweise)
        # DER HAUSANTEIL AN GRUNDLAGE UND KI-BILD (Video-Befund L4-2) — gleich gebaut.
        _hausanteil_eintragen(qa, geometrie_urteil, je_kamera, hinweise)
        # DAS HAUS NICHT WIEDERZUERKENNEN (auf-20261020-295, N2) — nur ein Satz.
        _wiedererkennung_eintragen(geometrie_urteil, je_kamera, hinweise)
        # DIE MESSSCHALTER (auf-20261021-298, B1) — nur mit Schalter, je Kamera ein Satz.
        _messschalter_eintragen(geometrie_urteil, je_kamera, hinweise)
        # OHNE GRUNDLAGENBILD (auf-20261021-312 B3) — an jedem Lauf, dessen Bild anders
        # gerechnet wurde als bestellt; bis dahin stand das nur als Feld in `angewandt.modus`.
        _modus_eintragen(geometrie_urteil, je_kamera, hinweise)
        # DER HIMMEL KAM AUS DER GRUNDLAGE (Entscheid 126) — Variante auf einer Grundlage,
        # deren Himmel von der Vorgabe abweicht: Auskunft, kein Vorbehalt.
        himmel = (((angewandt or {}).get("messschalter") or {}).get("himmel_sichtbar") or {}) \
            if isinstance(angewandt, dict) else {}
        if himmel.get("herkunft") == HERKUNFT_GRUNDLAGE and himmel.get("grund") \
                and himmel["grund"] not in hinweise:
            hinweise.append(himmel["grund"])
        # DIE FORM WEICHT VOM GRUNDBILD AB (Ergebnisse 337/339) — je Kamera ein Satz, wenn die
        # Kanten des KI-Bilds unter der Deckungsschwelle liegen.
        _deckung_eintragen(geometrie_urteil, je_kamera, hinweise)
        # DIE FENSTER DES GRUNDBILDS UEBERMALT (Mac-Befund 23.10.2026) — je Kamera ein Satz,
        # wenn am Glas des ID-Passes weniger als die Haelfte gehalten ist.
        _fenster_eintragen(geometrie_urteil, je_kamera, hinweise)
        # INS ERGEBNIS, NICHT NUR IN DEN BEFUND (Ergebnis 339): der Satz der Stoff-Variante und
        # der Satz, wenn der Bildeingang wegen der Lizenz des Modells entfiel (Entscheid 138).
        for satz in ergebnis_saetze_der_szene(angewandt):
            if satz not in hinweise:
                hinweise.append(satz)
        for satz in hinweise[vorher:]:
            qa["verdict"].setdefault("hinweise", []).append(satz)

    ergebnis = {
        "schema": SCHEMA_ERGEBNIS,
        "job_id": job_id,
        "images": list(bilder or []),
        "qa": qa,
        "hinweise": tuple(hinweise),
    }
    if zeiten:
        ergebnis["timings"] = dict(zeiten)

    # QA JE KAMERA — seit dem 03.09.2026 in ihrem Vertrag, bei uns bis zum 11.09. nicht
    # gesendet. Acht Tage lang war der Posten `B5` als IHRE Vertragsänderung geführt,
    # während er längst unserer war.
    #
    # NEBEN dem qa-Block und nicht darin: Ihr Entscheid sagt woertlich, der bestehende
    # `qa`-Block bleibe BYTE-IDENTISCH — ein Feld darin hinzuzufuegen waere genau das
    # nicht. Das ist ein SCHLUSS aus ihrem Satz und keine Angabe von ihnen; die Rueckfrage
    # laeuft (`auf-20260911-105`). Steht es bei ihnen anders, ist es eine Zeile.
    # DIE ZWEI TORE — neben dem `qa`-Block und nicht darin, aus demselben Grund wie
    # `qa_je_kamera`: Der bestehende Block bleibt byte-identisch. Was hier dazukommt, ist
    # keine Berichtigung des alten Urteils, sondern die zweite Frage, die es nie gestellt
    # hat (R3, 18.09.2026).
    #
    # AUF DEM PRODUKTWEG KOMMT DAS URTEIL AM KAMERAURTEIL (Durchsicht 22.09.2026): Bis
    # dahin reichte niemand `zwei_tore_urteil` durch, und der Block fehlte in jedem
    # Ergebnis, das an die fremde Warteschlange ging. Er stammt von DERSELBEN Kamera wie
    # der `qa`-Block — sonst stuenden unter `geom_iou` zwei Zahlen zweier Kameras, und
    # `_pruefe_ein_name_eine_zahl` meldete zu Recht einen Widerspruch.
    vom_kameraurteil = (zwei_tore_urteil is None and isinstance(geometrie_urteil, dict)
                        and URTEIL_ZWEI_TORE in geometrie_urteil)
    if vom_kameraurteil:
        zwei_tore_urteil = geometrie_urteil[URTEIL_ZWEI_TORE]
    if zwei_tore_urteil is not None or vom_kameraurteil:
        # `None` vom Kameraurteil heisst NICHT GEMESSEN: `als_zwei_tore_block` meldet
        # dann `status: fehlt`, `passed: None` und einen Grund — keinen leeren Block.
        ergebnis[FELD_ZWEI_TORE] = als_zwei_tore_block(zwei_tore_urteil)
        if vom_kameraurteil:
            ergebnis[FELD_ZWEI_TORE]["camera"] = geometrie_urteil.get("kamera")
            _andere_kameras_einrechnen(ergebnis[FELD_ZWEI_TORE], je_kamera,
                                       geometrie_urteil.get("kamera"))
        _pruefe_ein_name_eine_zahl(ergebnis[FELD_ZWEI_TORE], geometrie_urteil)

    saetze = _qa_je_kamera(job_id, je_kamera) if je_kamera else None
    if saetze:
        ergebnis["qa_je_kamera"] = saetze
    # DIE EBENEN (E124, Schritt 1) — eigenes Feld, nicht `images`; nur, wenn bestellt.
    # Ein fehlendes Feld heisst «nichts gesagt», nicht «keine Ebenen» (ihre Bedingung b).
    if ebenen:
        ergebnis["ebenen"] = [{k: v for k, v in e.items() if k != "grund" or not e.get("datei")}
                              for e in ebenen]
        _ebenen_mit_lieferung(saetze, ebenen)
    # DER LIEFERSTATUS DES AUFTRAGS — immer gesetzt (23.09.2026). Fehlt das Feld, greift
    # drueben die Vorgabe 'geliefert', und die galt bis heute fuer jedes unserer
    # Ergebnisse, auch fuer eines ohne Bild. Siehe `_lieferstatus_des_auftrags`.
    ergebnis["lieferstatus"], ergebnis["lieferstatus_grund"] = (
        _lieferstatus_des_auftrags(saetze, uebersprungen=uebersprungen,
                                   anzahl_bilder=len(ergebnis["images"])))
    ergebnis.update(engine_felder(engine))
    # DIE GRUNDLAGE DES LAUFS (Nr. 85, Vertrag 20.10.2026): `{id, wiederverwendet}`, nur wenn
    # Blender gerechnet oder eine Grundlage geholt wurde — sonst fehlt das Feld.
    if isinstance(grundlage, dict) and grundlage.get("id"):
        ergebnis["grundlage"] = {"id": str(grundlage["id"]),
                                 "wiederverwendet": grundlage.get("wiederverwendet") is True}
    # DIE GUETE (Entscheid 104, Vertrag 20.10.2026): nur, wenn der Auftrag sie trug — ein
    # Ergebnis ohne das Feld ist eines von vor dem Schalter, und dort gilt «voll».
    if guete in GUETEN:
        ergebnis["guete"] = guete
    # WAS DER HEIM-PC WIRKLICH GERECHNET HAT (Knoten Stimmung, Kamera, Oberflaeche;
    # 20.10.2026). Der Vertrag hat fuer diese Felder keine Vorgaben — der Heim-PC setzt sie
    # und nennt sie hier: `{environment?, cameras_auto?, materialien?}`, nur was bestellt war.
    if isinstance(angewandt, dict) and angewandt:
        ergebnis["angewandt"] = angewandt
        # DAS FREIE BILD (Entscheid 149): oberste Ebene, nur wenn wahr — wie
        # `engine_license_open`. Ein Leser, der `angewandt` nicht kennt, sieht es trotzdem.
        if isinstance(angewandt.get("freies_bild"), dict):
            ergebnis["freies_bild"] = True
    return ergebnis


def als_abweisung(job_id: str, grund: str, *, angewandt=None) -> dict:
    """Ein Ergebnis fuer einen Auftrag, der **vor** dem Rechnen abgewiesen wurde (Entscheid 113).

    Anlass: Fehlt ein Himmelsbild oder eine Textur am Rechner, endet der Auftrag mit Satz —
    und die Oberflaeche liest den Grund am Ergebnis (``lieferstatus_grund``), nicht nur am
    Laufzettel. Keine Bilder, ``lieferstatus: 'fehlgeschlagen'``, der Satz auch vorn in
    ``verdict.reason``.
    """
    ergebnis = als_ergebnis(job_id, [], angewandt=angewandt)
    ergebnis["lieferstatus"] = LIEFERSTATUS_FEHLGESCHLAGEN
    ergebnis["lieferstatus_grund"] = str(grund)
    verdict = ergebnis["qa"].setdefault("verdict", {"passed": False, "reason": ""})
    verdict["passed"] = False
    verdict["reason"] = f"ABGEWIESEN: {grund} {verdict.get('reason') or ''}".strip()
    return ergebnis


#: Der Anfang des Urteilssatzes einer Vorschau — dasselbe Wort, das am Bild steht.
VORSCHAU_ANFANG = "VORSCHAU"


def vorschau_satz(vermerk) -> str:
    """Der Satz, mit dem ``verdict.reason`` einer Vorschau beginnt (Entscheid 104a).

    Nennt, womit gerechnet wurde, soweit der Vermerk es weiss — Bildmodell, Schritte,
    Grösse des KI-Bilds —, und dass geprüft wurde wie bei jedem Bild.
    """
    teile = []
    if isinstance(vermerk, dict):
        if vermerk.get("backbone"):
            teile.append(str(vermerk["backbone"]))
        if vermerk.get("schritte"):
            teile.append(f"{vermerk['schritte']} Schritte")
        if vermerk.get("seed") is not None:
            teile.append(f"ein Startwert ({vermerk['seed']})")
        ki = vermerk.get("ki_groesse")
        if isinstance(ki, (list, tuple)) and len(ki) == 2:
            teile.append(f"KI-Bild {ki[0]} x {ki[1]}")
    womit = f" ({', '.join(teile)})" if teile else ""
    return (f"{VORSCHAU_ANFANG}: schnell gerechnet{womit}, geprueft wie jedes Bild. Fuer "
            f"das fertige Bild 'Voll' waehlen.")


def engine_felder(engine) -> dict:
    """``engine_used``, ``engine_license``, ``guidance_applied`` — oberste Ebene, alle optional.

    Zugesagt vom Integrator in der Antwort auf ``auf-20260923-155`` (F7, 29.09.2026), mit
    ihren Namen und zwei Bedingungen: oberste Ebene, und ``guidance_applied`` ist ein
    Boolean und **nie** ``null`` — weiss es der Lauf nicht, fehlt das Feld. Dasselbe gilt
    hier für alle drei: Was nicht bekannt ist, wird weggelassen, nicht geraten.
    """
    if not isinstance(engine, dict):
        return {}
    felder = {}
    if isinstance(engine.get("name"), str) and engine["name"]:
        felder["engine_used"] = engine["name"]
    if isinstance(engine.get("lizenz"), str) and engine["lizenz"]:
        felder["engine_license"] = engine["lizenz"]
    if isinstance(engine.get("fuehrung"), bool):
        felder["guidance_applied"] = engine["fuehrung"]
    # E128: nur wenn wahr — ein `false` hiesse «geprüft und frei», und das sagt hier
    # niemand. Vorgeschlagener Name, Vertragsfrage gestellt am 30.09.2026.
    if engine.get("lizenz_offen") is True:
        felder["engine_license_open"] = True
    return felder


def nur_vertragsfelder(ergebnis: dict) -> dict:
    """Unser Ergebnis ohne die Felder, die im fremden Vertrag nicht vorgesehen sind.

    Ihr Schema ist mit ``zod`` gebaut und lässt Zusatzfelder in der Regel durch — aber
    „in der Regel" ist keine Zusage. Wer strikt senden will, nimmt diese Fassung; wer
    die Hinweise braucht, das volle Wörterbuch.
    """
    aus = {k: v for k, v in (ergebnis or {}).items() if k != "hinweise"}
    # IHRE WOERTER AN DER AUSSENGRENZE (Antwort auf auf-142, 29.09.2026). Drinnen bleibt
    # die dreiwertige Form — ihre Proben tragen den Unterschied zwischen «nicht gemessen»
    # und «durchgefallen»; hinaus geht, was ihr Vertrag lesen kann.
    if isinstance(aus.get(FELD_ZWEI_TORE), dict):
        aus[FELD_ZWEI_TORE] = tore_in_ihren_worten(aus[FELD_ZWEI_TORE])
    if isinstance(aus.get("qa"), dict):
        aus["qa"] = _qa_mit_status(aus["qa"])
    if isinstance(aus.get("qa_je_kamera"), list):
        aus["qa_je_kamera"] = [_qa_mit_status(s) if isinstance(s, dict) else s
                               for s in aus["qa_je_kamera"]]
    return aus


#: Unsere Tor-Woerter → ihre drei (``render-result.ts:218``). Ihre Bedingung aus der Antwort
#: auf auf-142 (V2): «keine vierte Schreibweise». ``degeneriert`` (gerechnet, aber die Zahl
#: traegt nichts) ist fuer sie ``not_measured``; das Wort steht weiter in ``fail_reasons``.
TOR_STATUS_IHRE = {STATUS_OK: "measured", STATUS_FEHLT: "not_measured",
                   STATUS_DEGENERIERT: "not_measured",
                   STATUS_NICHT_ANWENDBAR: "not_applicable"}
TOR_STATUSFELDER = ("status", "rho_mask_status", "geom_iou_status", "counter_check_status")


def tore_in_ihren_worten(block: dict) -> dict:
    """``geometry_gates`` in ihrer Form: drei Statuswoerter, ``passed`` immer Boolean.

    * Leere Werte (``None``) werden **weggelassen**, nicht als ``null`` gesendet — bei ihnen
      ist ``null`` in einem optionalen Feld ungueltig, Weglassen richtig (E123).
    * ``passed: None`` («nicht entscheidbar») wird ``false`` — ihr ``passed`` ist Boolean
      (V3). Damit das ``false`` nicht als «durchgefallen» gelesen wird, sagt ``status`` es:
      ``not_measured``, wenn nichts gemessen ist; ``not_applicable``, wenn gemessen wurde,
      die Gegenprobe aber zeigt, dass die Messung hier nicht trennt. **Diese zweite
      Zuordnung ist unser Vorschlag, nicht ihre Angabe** — im Ergebnisblatt zur Bestaetigung
      gestellt.
    """
    aus = {k: v for k, v in block.items() if v is not None}
    for feld in TOR_STATUSFELDER:
        if feld in aus:
            aus[feld] = TOR_STATUS_IHRE.get(aus[feld], "not_measured")
    if block.get("passed") is None:
        aus["passed"] = False
        if aus.get("status") == "measured":
            aus["status"] = "not_applicable"
    return aus


def _qa_mit_status(block: dict) -> dict:
    """``geometry.status`` setzen, das ihr Vertrag seit dem 03.09.2026 fuehrt (V3).

    Ohne das Feld liest ihre Kamerazeile ein ungeprueftes ``passed: false`` als
    «durchgefallen». ``measured`` nur, wenn eine Zahl da ist.
    """
    geo = block.get("geometry")
    if not isinstance(geo, dict) or "status" in geo:
        return block
    gemessen = geo.get("geometry_fidelity") is not None
    return dict(block, geometry=dict(geo, status="measured" if gemessen else "not_measured"))


def pruefe_job_id(job_id) -> dict:
    """Passt unsere Auftragskennung in ihre Warteschlange?

    Ihr Schema verlangt wörtlich ``^vis-\\d+-[0-9a-f]{6}$``. Eine abweichende Kennung
    wird dort **abgewiesen** — und zwar erst in ihrer Warteschlange, nicht bei uns.

    Es wird **nicht** umbenannt: Eine Kennung ist die Klammer zwischen Auftrag, Bildern
    und Protokoll. Wer sie an der Naht still ändert, macht ein Ergebnis unauffindbar.

    Gefragt wird über :func:`ist_fremde_job_id` — dieselbe Auskunft, die auch
    ``bruecke`` über seine Auftragsordner einholt. Bis zum 22.09.2026 stand die Regel
    hier und dort und in ``kosmo_naht`` je einmal ausgeschrieben; siehe
    :data:`FREMDE_JOB_ID`.
    """
    if not ist_fremde_job_id(job_id):
        return {"passt": False, "begruendung": (
            f"Die Auftragskennung {job_id!r} entspricht nicht der Form der fremden "
            f"Warteschlange (vis-<zahl>-<sechs Hexziffern>). Der Auftrag würde dort "
            f"abgewiesen. Hier wird NICHT umbenannt — eine Kennung ist die Klammer "
            f"zwischen Auftrag, Bildern und Protokoll.")}
    return {"passt": True, "begruendung": ""}
