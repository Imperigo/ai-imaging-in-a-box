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
    urteil = _backbone.pruefe_lizenz(unser)
    return {"name": unser, "bekannt": True, "zulaessig": urteil["zulaessig"],
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
         "interior", "gelaende", "komposition", "innenansichten"),
    "geometry": ("path", "format", "up_axis"),
    "render": ("resolution", "faithful", "samples", "sun",
               "environment", "himmel", "belichtung", "rauschschwelle"),
    "style": ("prompt", "mode", "refs"),
    "vis": ("backbone", "skip", "upscale", "research_only"),
    # Belegt ist genau EIN Unterfeld (auf-31 R3, auf-91 V1): `rooms`, gesendet als
    # "auto". Ein `view` (frontal/ueber Eck) ist drueben ausdruecklich NICHT gebaut —
    # kaeme es trotzdem, faellt es hier als unbekannt auf und nicht still weg.
    "interior": ("rooms",),
}

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
    "render.environment": (
        "Bekannt (preset, hdri, intensitaet, rotationGrad — auf-44), aber von unserer "
        "Kette nicht gelesen: Ein bestelltes Umgebungslicht fiele still weg. Noetig waere "
        "ein Weg, Umgebungsbilder mit permissiver Lizenz zu uns zu bringen (Regeln 1 und 3)."),
    "render.himmel": (
        "Der Name ist bekannt (auf-104), Form und Bedeutung sind es nicht, und unsere "
        "Kette liest das Feld nicht. Wir raten nicht, was es verlangt."),
    "render.belichtung": (
        "Der Name ist bekannt (auf-104), Form und Bedeutung sind es nicht, und unsere "
        "Kette liest das Feld nicht. Wir raten nicht, was es verlangt."),
    "render.rauschschwelle": (
        "Der Name ist bekannt (auf-104), Form und Bedeutung sind es nicht, und unsere "
        "Kette liest das Feld nicht. Wir raten nicht, was es verlangt."),
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
#: entweder ``"auto"`` oder eine Liste von Kameraspezifikationen, die
#: :func:`spec_zu_kamera` einzeln prüft.
NICHT_DURCHSUCHT = ("render.sun", "cameras")


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
    return tuple(gefunden)


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


def lies_szene(fremd: dict, *, streng: bool = True) -> dict:
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

    Raises:
        SzenenError: kein Wörterbuch, oder ``geometry.path`` fehlt. Ohne Geometrie gibt
            es nichts zu rendern; alles andere hat im fremden Vertrag Vorgabewerte.
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
    if not pfad:
        raise SzenenError("render-scene ohne 'geometry.path' — es gibt nichts zu rendern.")
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
        aufl, hinweis = _auf_raster([zahl for zahl, _ in masse])
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
    fremd_bb = vis.get("backbone", "qwen")
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

    sonne = render.get("sun")
    if sonne is not None:
        # Bedient wird der Sonnenstand seit dem 26.08.2026 — aber unter EINER Annahme,
        # und die stammt nicht aus dem fremden Vertrag. Die beiden ueblichen Konventionen
        # unterscheiden sich um 180 Grad und vertauschen damit Vormittag und Nachmittag.
        # Das ist eine Warnung ueber DIESEN Auftrag und keine Vertragsvorgabe: Sie
        # erscheint nur, wenn wirklich eine Sonne bestellt wurde.
        warnungen.append(
            f"Sonnenstand {sonne!r} wird bedient, der Azimut aber unter der ANNAHME "
            f"'{_sonne.VORGABE_KONVENTION}' (0 Grad im Sueden, positiv nach Westen). Ob "
            f"der fremde Vertrag von Norden zaehlt, ist NICHT geklaert — der Unterschied "
            f"betraegt 180 Grad und vertauscht Vormittag und Nachmittag. Die benutzte "
            f"Konvention steht im Bericht des Runners (Feld 'sonne').")
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
    # Die Referenzbilder: Eine Zahl warf TypeError aus `list(...)`, ein Text zerfiel
    # still in einzelne Zeichen (23.09.2026).
    refs = stil.get("refs") or []
    if isinstance(refs, (list, tuple)):
        referenzen = list(refs)
    else:
        referenzen = []
        maengel.append(
            f"'style.refs' ist {refs!r} und keine Liste. Als Text zerfiele es in "
            f"einzelne Zeichen; welche Bilder gemeint sind, raten wir nicht.")

    return {
        "geometrie": pfad,
        "format": fmt or None,
        "out": fremd.get("out"),
        "kameras": kameras,
        # `None` heisst hier NICHT GELESEN — dann steht der Grund unter `maengel`.
        "aufloesung": aufl[0],
        "hoehe": aufl[1],
        "samples": samples,
        "controlnet_staerke": treue,
        "prompt": sprachbefund["uebersetzt"],
        "prompt_original": sprachbefund["original"],
        "prompt_sprache": sprachbefund,
        "prompt_bauteile": tuple(bauteile),
        "stil_modus": wert_oder(stil, "mode", "none"),
        "stil_referenzen": referenzen,
        "backbone": bb["name"],
        "ueberspringen": schalter["skip"],
        "hochskalieren": schalter["upscale"],
        "sonne": sonne,
        "innenraum": innenraum,
        "innen_bestellt": innen_bestellt,
        "gelaende_erwartet": gelaende,
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
    "geometrie": "abholer: Pfad der glb",
    "format": "lies_szene selbst — unbekannte Formate werden als Mangel abgelehnt; "
              "'ifc' waehlt seit 22.09.2026 in bruecke.lies_auftrag model.ifc und in "
              "abholer.verarbeiter die Umwandlung IFC → glb (seams.ifc_zu_glb)",
    "out": "abholer: Ausgabeverzeichnis",
    "kameras": "abholer.verarbeiter → Kameraaufgaben",
    "aufloesung": "seams.glb_zu_multipass(aufloesung=…)",
    "hoehe": "seams.glb_zu_multipass(hoehe=…)",
    "samples": "seams.glb_zu_multipass(samples=…)",
    "controlnet_staerke": "render.RenderAuftrag(controlnet_staerke=…)",
    "backbone": "render.RenderAuftrag(backbone=…)",
    "prompt": "render.RenderAuftrag(prompt=…)",
    "prompt_original": "befund.json",
    "prompt_sprache": "befund.json und befund_kurz",
    "prompt_bauteile": "befund.json und befund_kurz",
    "vertragsvorgaben": "tools/abholen.py: einmal pro Lauf, nicht je Auftrag",
    "warnungen": "Antwort des Auftrags",
    "maengel": "halten den Lauf auf",
    # Seit 26.08.2026 — vorher stand es in STEHENGEBLIEBEN, und der Abholer meldete das
    # von sich aus: «BESTELLT UND NICHT AUSGEFUEHRT». Im Lauf vom 25.08. wurde es dann
    # belegt (auf-vis-20260825-15, Posten 2): Wer abbestellt, bekommt geliefert — und
    # zahlt die GPU-Zeit.
    "ueberspringen": "abholer.verarbeiter: der Auftrag wird NICHT gerendert",
    # Seit 26.08.2026 — vorher der GEFAEHRLICHSTE der stehengebliebenen Felder, weil das
    # Bild danach richtig AUSSAH (auf-vis-20260825-15 Posten 5.3).
    "sonne": "seams.glb_zu_multipass(sonne=…) → blender_depth_stage --sonne-hoehe/-azimut",
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
            f"Kamera {name!r}: {status!r}, obwohl {ist} von {soll} Bildern da sind. "
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
            f"NICHT FESTGESTELLT: {len(lieferungen)} von {len(saetze or ())} Kameras "
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
        f"{status.count(LIEFERSTATUS_GELIEFERT)} von {len(status)} Kameras geliefert, "
        f"{zahl(ist)} von {zahl(soll)} Bildern — {fehlend}")


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
        for feld in ("geometry", "style"):
            if feld in block:
                satz[feld] = block[feld]
        # DIE LIEFERUNG DIESER KAMERA (23.09.2026) — nur, wenn der Aufrufer sie kennt;
        # geprueft in `_lieferung_je_kamera`. Fehlt sie, fehlen die Felder und der
        # Auftrag meldet `lieferstatus: null`, statt eine Lieferung zu erfinden.
        lieferung = _lieferung_je_kamera(eintrag)
        if lieferung is not None:
            satz.update(lieferung)
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
    """Der Satz fuer ``verdict.reason`` zu einem :data:`URTEIL_INNENANSICHT`-Vermerk — oder ``""``.

    In ``verdict.reason`` und nicht in einem eigenen Feld: Ein Zusatzfeld in
    ``qa_je_kamera`` wuerde drueben beim Einlesen still abgestreift (``z.object``, nicht
    strikt — erg-20260917-49, render-result.ts 366-393), ``reason`` ist ein Vertragsfeld
    und wird angezeigt.

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
                f"gewaehlt — ob eine Kamera innen steht, prueft diese Seite nicht.")
    if not gerendert:
        return (f"INNENANSICHT BESTELLT: Standpunkt im Raum {vermerk.get('raum')!r} "
                f"({vermerk.get('art')}) aus 'interior' {vermerk.get('bestellt')!r} "
                f"gerechnet, nicht gerendert — zu diesem Standpunkt gibt es kein Bild.")
    return (f"INNENANSICHT: Standpunkt im Raum {vermerk.get('raum')!r} "
            f"({vermerk.get('art')}), aus 'interior' {vermerk.get('bestellt')!r} aus den "
            f"Raeumen der IFC gerechnet. Das Bild zeigt den Raum von innen, nicht das "
            f"Gebaeude von aussen.")

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
    if not gemessen:
        gruende.append(f"{praefix}_nicht_gemessen")
    elif not bestanden:
        gruende.append(f"{praefix}_unter_schwelle")
    return {praefix: wert if ist_zahl else None,
            f"{praefix}_threshold": tor.get("schwelle"),
            f"{praefix}_status": STATUS_OK if gemessen else STATUS_DEGENERIERT,
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


def _lage_ohne_urteil(geometrie_urteil: dict) -> str:
    """WARUM ein Geometrieurteil ``bestanden: None`` traegt — der Satz fuer ``reason``.

    Herausgezogen am 22.09.2026 aus :func:`als_ergebnis`, damit derselbe Satz auch fuer
    jede andere Kamera in ``qa_je_kamera`` gilt (siehe :func:`_vorbehalte_je_kamera`).
    Der Wortlaut ist unveraendert.
    """
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
    siehe ``abholer._sollkennung``): Sie traegt dasselbe Bild und dasselbe Torurteil. Faellt
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


def als_ergebnis(job_id: str, bilder, *, geometrie_urteil=None, stil_urteil=None,
                 zeiten=None, uebersprungen: bool = False,
                 nicht_gerendert=(), je_kamera=None,
                 zwei_tore_urteil=None) -> dict:
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
            "geom_iou": geometrie_urteil.get("geom_iou"),
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
        if geometrie_urteil.get("nullanker") is None:
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
        teile.append(f"Geometrie {qa['geometry']['geometry_fidelity']} "
                     f"gegen {qa['geometry']['threshold']}")
    if qa.get("style"):
        if qa["style"]["style_score"] is None:
            # Kein Skalar, also auch kein "x gegen y" — der Satz muss sagen, WOMIT
            # geprüft wurde, sonst liest sich ein leeres Feld wie ein Fehler.
            teile.append(f"Stil gegen den Belichtungsrahmen ({qa['style']['method']}), "
                         f"ohne Ähnlichkeitszahl")
        else:
            teile.append(f"Stil {qa['style']['style_score']} gegen "
                         f"{qa['style']['threshold']} ({qa['style']['method']})")
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
    if _geo.get("score") is None and _paar.get("gemessen") is True:
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

    if uebersprungen:
        # Vor allen anderen: Wer abbestellt hat, braucht keine Erklaerung darueber, was
        # nicht gemessen wurde. Er braucht die Bestaetigung, dass nichts LIEF.
        grund = ("ABBESTELLT: Der Auftrag trug 'skip: true' und wurde nicht gerechnet. "
                 "'passed: false' heisst hier weder durchgefallen noch ungeprueft — es "
                 "war nichts bestellt. Es ist keine GPU-Zeit angefallen.")
    elif not messbar and nicht_gerendert:
        # Es IST etwas gemessen worden — nur eben vor dem Bild, und mit dem Ergebnis,
        # dass kein Bild entstehen soll. Der Satz «keine QA gelaufen» wäre hier eine
        # Untertreibung, die wie ein Fehler aussieht.
        grund = "; ".join(teile)
    elif not messbar:
        grund = ("Keine QA gelaufen — weder Geometrie noch Stil wurden gemessen. "
                 "'passed: false' heisst hier NICHT durchgefallen, sondern ungeprüft.")
    elif qa.get("geometry") and geometrie_urteil.get("nullanker") is None:
        # Der Satz muss dort stehen, wo das Abzeichen gelesen wird — nicht nur in einem
        # Übergabeblatt, das niemand aufschlägt, während er auf ein Häkchen sieht.
        teile.append("Geometrie-Schwelle NICHT kalibriert (keine Nullprobe, "
                     "siehe hinweise)")
        grund = "; ".join(teile)
        hinweise.append(grund)
    else:
        grund = "; ".join(teile)

    # DIE INNENANSICHT, wenn `interior` bestellt war (22.09.2026). Nach allen Zweigen
    # oben angehaengt, weil sie keinen davon ersetzt: Sie sagt, WOHER der Standpunkt kam,
    # nicht wie es abgeschnitten hat. Bei `uebersprungen` nicht — abbestellt ist
    # abbestellt, und die Kette liefert dort gar kein Urteil.
    #
    # OB ES EIN BILD GIBT, liest der Satz am `bild_png` DESSELBEN Urteils (Durchsicht
    # 23.09.2026) — bis dahin hiess es auch ohne Bild «Das Bild zeigt den Raum».
    _vermerk_urteil = geometrie_urteil or {}
    innen = innenansicht_satz(_vermerk_urteil.get(URTEIL_INNENANSICHT),
                              gerendert=bool(_vermerk_urteil.get("bild_png")))
    if innen and not uebersprungen:
        grund = f"{grund}; {innen}" if grund else innen
        hinweise.append(innen)

    qa["verdict"] = {"passed": bestanden, "reason": grund}

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
    # DER LIEFERSTATUS DES AUFTRAGS — immer gesetzt (23.09.2026). Fehlt das Feld, greift
    # drueben die Vorgabe 'geliefert', und die galt bis heute fuer jedes unserer
    # Ergebnisse, auch fuer eines ohne Bild. Siehe `_lieferstatus_des_auftrags`.
    ergebnis["lieferstatus"], ergebnis["lieferstatus_grund"] = (
        _lieferstatus_des_auftrags(saetze, uebersprungen=uebersprungen,
                                   anzahl_bilder=len(ergebnis["images"])))
    return ergebnis


def nur_vertragsfelder(ergebnis: dict) -> dict:
    """Unser Ergebnis ohne die Felder, die im fremden Vertrag nicht vorgesehen sind.

    Ihr Schema ist mit ``zod`` gebaut und lässt Zusatzfelder in der Regel durch — aber
    „in der Regel" ist keine Zusage. Wer strikt senden will, nimmt diese Fassung; wer
    die Hinweise braucht, das volle Wörterbuch.
    """
    return {k: v for k, v in (ergebnis or {}).items() if k != "hinweise"}


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
