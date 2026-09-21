"""Die Tür, an der ein Modell hereinkommt — **und ein Satz darüber, ob damit zu rechnen ist.**

**Der Anlass** (Bestandsaufnahme 19.09.2026, gemessen und nicht geschätzt): Neunzehn
Stellen im Kern nehmen eine Modelldatei entgegen. **Genau zwei** sehen hinein, bevor
gerechnet wird. Der IFC-Eingang prüft weder Existenz noch Endung noch Inhalt; eine JPG
mit dem Namen ``model.glb`` kommt mit **null Mängeln** durch; ``.skp``, ``.3dm`` und
``.dwg`` haben keinen eigenen Satz und laufen als kaputte IFC ins Leere.

Und die Bausteine für genau diese Prüfung lagen fertig da — mit **null
Produktivaufrufern**: :mod:`aiimaging.herkunft` liest Format, Einheit und Hochachse aus
dem Dateikopf, :mod:`aiimaging.glbbox` rechnet Hüllbox und Geländetrennung in
Millisekunden.

    *Der Prototyp misst besser, als er prüft.*

Dieses Modul ist die Antwort darauf. Es beantwortet **eine** Frage:

    **Ist mit dieser Datei zu rechnen — und wenn nein, warum nicht?**

**Was es ausdrücklich NICHT tut:**

* Es wandelt nichts um. Keine Konversion, kein Subprozess, kein ``.venv-ifc``, kein
  Blender, keine GPU. Ein Sichtgang, der eine halbe Stunde dauert, ist kein Sichtgang.
* Es repariert nichts. Eine Datei mit falscher Einheit wird **gemeldet**, nicht skaliert —
  ein stillschweigend behobener Fehler wandert unbemerkt durch die ganze Kette.
* Es entscheidet nicht über die Hochachse. Es sagt nur, ob sie feststeht.

**Was «brauchbar» hier heisst, und die drei Antworten sind nicht zwei:**

``True``
    Format erkannt, Kopf lesbar, nichts spricht dagegen. Das ist **keine Zusage**, dass
    der Lauf gelingt — nur, dass er sich lohnt.
``False``
    Es spricht etwas dagegen, und es steht in ``grund``. Hier wird abgeraten.
``None``
    **NICHT ENTSCHEIDBAR.** Die Datei liess sich nicht weit genug ansehen, um zu
    urteilen. *Das ist weder ein Ja noch ein Nein* — die dritte Antwort dieses Projekts,
    angewandt auf den Einlass.

Regel 4 (der Kern ist eine Bibliothek): Alles hier läuft aus reinem Python, ohne dass
eine Oberfläche, ein fremdes Environment oder eine Grafikkarte da sein muss.
"""
from __future__ import annotations

from pathlib import Path

from aiimaging import herkunft

__all__ = [
    "EIGENE_UMWANDLUNG", "EinlassError", "FASSUNGSABHAENGIG", "FREMDE_FORMATE",
    "GROESSE_WARNSCHWELLE_BYTE",
    "KOPF_LESEFENSTER_BYTE", "UNSERE_FORMATE", "sichte",
]


class EinlassError(ValueError):
    """Der Sichtgang selbst ist gescheitert — nicht die Datei.

    **Der Unterschied ist die ganze Sorgfalt dieses Moduls.** Eine unbrauchbare Datei ist
    ein *Befund* und kommt als ``brauchbar: False`` zurück; ein Sichtgang, der nicht
    stattfinden konnte, ist ein *Fehler des Werkzeugs* und fliegt. Wer beides
    zusammenwirft, kann später nicht mehr unterscheiden, ob die Datei schlecht war oder
    die Prüfung.
    """


#: Die Formate, mit denen dieses Projekt rechnen kann. Gleichlautend mit
#: ``kosmo_szene.UNSERE_FORMATE`` — hier noch einmal genannt, weil ein Einlass, der seine
#: eigene Antwort aus einem Vertragsmodul holt, von dessen Änderungen abhängt.
UNSERE_FORMATE = ("glb", "gltf", "ifc")

#: Ab welcher Dateigrösse gewarnt wird. **GESETZT, nicht gemessen** — und der Grund, dass
#: sie überhaupt hier steht, ist ein Befund: Bis zum 19.09.2026 gab es im ganzen Kern
#: **keine einzige Grössengrenze**. Was stattdessen zuschlug, war die Zeitfrist von 300 s,
#: und die meldete sich als rohe Bibliotheksausnahme statt als Satz.
#:
#: 500 MB ist die Grössenordnung, ab der ein IFC-Import auf einem Laptop Minuten statt
#: Sekunden braucht. **Gewarnt wird, nicht gesperrt:** Wer eine grosse Datei hat, hat sie,
#: und eine Sperre wäre eine Entscheidung über fremde Geduld.
GROESSE_WARNSCHWELLE_BYTE = 500 * 1024 * 1024

#: Wieviel vom Dateianfang gelesen wird, um das Format am **Inhalt** zu erkennen.
#: Die längste Kennung unten ist 24 Byte; 512 gibt Luft für Dateien, die ein
#: Byte-Reihenfolge-Zeichen oder Leerraum voranstellen.
KOPF_LESEFENSTER_BYTE = 512

#: Formate, die wir **nicht selbst lesen, aber selbst umwandeln** — seit dem 21.09.2026.
#:
#: **Warum es diese dritte Kategorie geben musste.** Bis zum 21.09.2026 kannte dieser
#: Sichtgang zwei Sorten: unsere Formate und fremde. Eine FBX fiel unter «fremd» und bekam
#: den Rat, sie doch bitte selbst in Blender nach glTF zu exportieren.
#:
#: Seit :mod:`aiimaging.importeur` existiert, ist dieser Rat falsch — **wir tun das
#: selbst**, über denselben Blender-Subprozess, der ohnehin läuft. Ein Türsteher, der
#: jemanden wegschickt, für den drinnen längst gedeckt ist, ist schlimmer als keiner: Er
#: macht die neue Fähigkeit unerreichbar und sieht dabei sorgfältig aus.
#:
#:     *Eine Fähigkeit, von der die Tür nichts weiss, gibt es für den Benutzer nicht.*
#:
#: **Kennung UND Endung müssen passen.** ``<?xml`` steht am Anfang jeder XML-Datei; nur
#: zusammen mit ``.dae`` oder ``.x3d`` ist daraus ein Modell zu schliessen. Der
#: Subprozess wählt seinen Importeur nach der Endung, und eine Datei, deren Endung er
#: nicht kennt, käme dort ohne Weg an.
#:
#: Formate ohne eigene Kennung (``.obj``, ``.ply``, ``.usda``, ``.abc``) stehen hier
#: **nicht**: Sie sind am Inhalt nicht zu erkennen und fallen darum in «nicht
#: entscheidbar» — und das lässt der Importeur durch, weil abgewiesen nur wird, was
#: sicher falsch ist.
#: Formate aus :data:`EIGENE_UMWANDLUNG`, deren Umwandlung an der **Blender-Fassung**
#: hängt. Gemessen am 21.09.2026 (`auf-20260921-126`): In Blender 5.2.1 sind Collada und
#: X3D **entfernt**, nicht umbenannt — Import wie Export. Blender 4.2 liest beide.
FASSUNGSABHAENGIG: dict[str, str] = {
    ".dae": "In Blender 5.2 ist Collada entfernt; Blender 4.2 liest es.",
    ".x3d": "In Blender 5.2 ist X3D entfernt; Blender 4.2 liest es.",
}

EIGENE_UMWANDLUNG: tuple[tuple[bytes, int, tuple[str, ...], str], ...] = (
    (b"Kaydara FBX Binary", 0, (".fbx",), "Autodesk FBX"),
    (b"PXR-USDC", 0, (".usd", ".usdc"), "USD (binär)"),
    (b"solid ", 0, (".stl",), "STL (Text)"),
    (b"<?xml", 0, (".dae", ".x3d"), "Collada bzw. X3D"),
)


def _eigene_umwandlung(anfang: bytes, endung: str) -> str | None:
    """Können **wir** diese Datei umwandeln? Der Name des Formats, oder ``None``."""
    for kennung, versatz, endungen, name in EIGENE_UMWANDLUNG:
        if anfang[versatz:versatz + len(kennung)] == kennung and endung in endungen:
            return name
    return None


#: Formate, die dieses Projekt **nicht** verarbeitet — aber beim Namen nennen kann.
#:
#: **Warum das mehr ist als Höflichkeit:** Eine ``.skp`` lief bis zum 19.09.2026 als
#: kaputte IFC ins Leere und endete in einem ``KeyError`` aus einer fremden Bibliothek.
#: Wer «SketchUp kann ich nicht» liest, weiss in einer Sekunde, woran er ist; wer einen
#: Stacktrace liest, hört auf.
#:
#: **HERKUNFT DER KENNUNGEN: GESETZT aus veröffentlichten Formatbeschreibungen, NICHT an
#: echten Dateien dieses Projekts gemessen.** Das ist eine schwächere Grundlage als der
#: Rest dieses Moduls, und sie steht hier ausdrücklich dabei.
#:
#: Die Bauart begrenzt den Schaden einer falschen Kennung: Getroffen wird nur bei
#: **exakter** Übereinstimmung am gemeldeten Versatz, und das Urteil lautet dann
#: ``brauchbar: False`` mit dem Satz «sieht aus wie …». Eine falsche Kennung führt also zu
#: einer Ablehnung, die es ohnehin gegeben hätte — nur mit einem falschen Namen darin. Sie
#: kann **kein** brauchbares Modell abweisen, denn unsere drei Formate werden vorher
#: erkannt.
FREMDE_FORMATE: tuple[tuple[bytes, int, str, str], ...] = (
    (b"3D Geometry File Format", 0, "Rhino (.3dm)",
     "Rhino kann glTF ausgeben: Datei → Exportieren als → glTF."),
    (b"AC10", 0, "AutoCAD-Zeichnung (.dwg)",
     "Eine DWG ist eine Zeichnung, kein Gebäudemodell — sie trägt keine Bauteile, nur "
     "Linien. Aus Revit oder ArchiCAD gibt es einen IFC-Export."),
    (b"Kaydara FBX Binary", 0, "FBX",
     "Dieses Werkzeug wandelt FBX selbst um — dafür muss die Datei aber auf .fbx enden. "
     "Datei umbenennen, dann geht sie von allein durch."),
    (b"BLENDER", 0, "Blender-Datei (.blend)",
     "In Blender selbst: Datei → Exportieren → glTF 2.0 (.glb)."),
    (b"SketchUp Model", 0, "SketchUp (.skp)",
     "SketchUp kann IFC ausgeben (Datei → Exportieren → IFC) — das ist der bessere Weg, "
     "weil dabei die Bauteile erhalten bleiben."),
    (b"PXR-USDC", 0, "USD (binär)",
     "Dieses Werkzeug wandelt USD selbst um — dafür muss die Datei auf .usd oder .usdc "
     "enden. Datei umbenennen, dann geht sie von allein durch."),
    (b"solid ", 0, "STL (Text)",
     "Mit der Endung .stl wandelt dieses Werkzeug die Datei selbst um. Es bleibt aber "
     "dabei: Eine STL trägt nur Dreiecke — keine Räume, keine Bauteile, keine "
     "Materialien. Für eine Architektur-Visualisierung ist IFC oder glTF der bessere Weg."),
    (b"<?xml", 0, "XML — vermutlich Collada (.dae) oder ein XML-Format",
     "Heisst die Datei .dae oder .x3d, wandelt dieses Werkzeug sie selbst um. Ohne diese "
     "Endung ist nicht zu erkennen, ob überhaupt Geometrie darin steht — jede XML-Datei "
     "fängt gleich an."),
    (b"\xff\xd8\xff", 0, "JPEG-Bild",
     "Das ist ein Bild und kein Modell. Stimmt der Dateiname?"),
    (b"\x89PNG", 0, "PNG-Bild",
     "Das ist ein Bild und kein Modell. Stimmt der Dateiname?"),
    (b"%PDF", 0, "PDF",
     "Ein PDF trägt keine Geometrie, mit der sich rechnen lässt."),
    (b"PK\x03\x04", 0, "ZIP-Archiv (oder ein Format, das darauf aufbaut)",
     "Falls das Modell darin liegt: erst auspacken."),
)


def _fremdes_format(anfang: bytes) -> tuple[str, str] | None:
    """Sieht der Dateianfang nach einem Format aus, das wir kennen, aber nicht können?

    ``None`` heisst **nicht** «unbekanntes Format» — es heisst «keine der bekannten
    fremden Kennungen passt». Eine unbekannte Datei bleibt unbekannt, und das ist ein
    eigener Befund.
    """
    for kennung, versatz, name, rat in FREMDE_FORMATE:
        if anfang[versatz:versatz + len(kennung)] == kennung:
            return name, rat
    return None


def _lies_anfang(pfad: Path) -> bytes:
    """Der Dateianfang — oder ein :class:`EinlassError`, wenn nicht einmal das geht."""
    try:
        with pfad.open("rb") as datei:
            return datei.read(KOPF_LESEFENSTER_BYTE)
    except OSError as fehler:
        raise EinlassError(
            f"{pfad.name} lässt sich nicht lesen: {fehler}. Das ist kein Urteil über die "
            f"Datei, sondern über den Zugriff darauf — Rechte, Laufwerk, Netzpfad."
        ) from fehler


def sichte(pfad) -> dict:
    """Eine Modelldatei ansehen und sagen, ob mit ihr zu rechnen ist.

    **Ohne Konversion, ohne Subprozess, ohne Blender, ohne GPU.** Gelesen werden der
    Dateianfang und — bei einem erkannten Format — der Kopf. Bei einer 500-MB-IFC ist das
    dasselbe wie bei einer 5-KB-IFC.

    Args:
        pfad: Die Datei. Sie muss nicht existieren — das ist einer der Befunde.

    Returns:
        Ein ``dict`` mit:

        ``brauchbar``
            ``True`` / ``False`` / ``None``. **``None`` heisst NICHT ENTSCHEIDBAR** und
            ist weder ein Ja noch ein Nein.
        ``grund``
            **Ein Satz für einen Menschen.** Keine Ausnahme, kein Stacktrace, kein
            Fachwort ohne Erklärung. Die Zielgruppe sind Architektinnen und Studierende.
        ``format``
            Der Name des Formats, **bestimmt am Inhalt und nicht an der Endung** — eine
            Endung ist eine Behauptung des Benennenden, der Dateianfang eine des
            Erzeugers. ``None``, wenn sich nichts erkennen liess.

            *Die Genauigkeit hängt davon ab, wie weit der Sichtgang gekommen ist:* Konnte
            der Kopf gelesen werden, steht hier die **enge** Angabe (``"glb"`` oder
            ``"gltf"``, ``"IFC"``). Brach er vorher ab, steht die **Familie**
            (``"glTF"``) — mehr war dann nicht festzustellen, und eine engere Angabe wäre
            geraten.
        ``endung_passt``
            ``True`` / ``False`` / ``None`` (keine Endung, oder Format unerkannt). Eine
            umbenannte Datei ist brauchbar, wenn ihr Inhalt stimmt — aber sie ist einen
            Hinweis wert, weil andere Werkzeuge der Endung glauben.
        ``groesse_byte``
            Die Dateigrösse, oder ``None``, wenn sie nicht zu ermitteln war.
        ``hochachse``
            Welche Achse oben ist, **wenn es feststeht** — sonst ``None``. Bei IFC folgt
            sie aus dem Format (ISO 16739), bei glTF ist sie nirgends erklärt.
        ``hochachse_steht_fest``
            ``True`` heisst: Der Lauf braucht keine Angabe. ``False`` heisst: **Ohne
            Angabe wird geraten, und eine falsche Angabe fällt nirgends auf.**
        ``kopf``
            Die volle Auskunft aus :mod:`aiimaging.herkunft`, wenn eine zu haben war.
        ``hinweise``
            Sätze, die nichts verhindern, aber jemand wissen sollte.
        ``naechster_schritt``
            Was zu tun ist. Bei ``brauchbar: False`` ist das der wichtigste Teil der
            Antwort — *eine Absage ohne Ausweg ist eine halbe Auskunft.*

    Raises:
        EinlassError: Nur, wenn der **Sichtgang** nicht stattfinden konnte — etwa weil
            die Datei nicht lesbar ist. Eine unbrauchbare Datei wirft **nicht**, sie
            kommt als Befund zurück.

    Beispiel::

        >>> from aiimaging import einlass
        >>> einlass.sichte("haus.ifc")["grund"]
        'IFC4, Längen in METRE, erzeugt mit …. Damit lässt sich rechnen.'
    """
    pfad = Path(pfad)
    hinweise: list[str] = []

    # ── Gibt es die Datei überhaupt? ─────────────────────────────────────────────────
    #
    # Zuerst, weil jede weitere Frage sie voraussetzt. Und ausdrücklich als BEFUND und
    # nicht als Ausnahme: Ein Tippfehler im Pfad ist der häufigste Fall überhaupt, und er
    # verdient einen Satz und keinen Traceback.
    if not pfad.exists():
        return _befund(
            brauchbar=False, format=None,
            grund=f"Es gibt keine Datei unter diesem Pfad: {pfad}",
            naechster_schritt="Pfad prüfen — meist ein Tippfehler oder ein Ordnerwechsel.",
            hinweise=hinweise)
    if pfad.is_dir():
        return _befund(
            brauchbar=False, format=None,
            grund=f"{pfad.name} ist ein Ordner und keine Datei.",
            naechster_schritt="Die Modelldatei darin angeben.",
            hinweise=hinweise)

    try:
        groesse = pfad.stat().st_size
    except OSError:
        # Die Grösse ist eine Auskunft, kein Tor. Fehlt sie, geht der Sichtgang weiter —
        # aber sie wird NICHT auf 0 gesetzt: Eine 0 wäre eine gemessene Null und hiesse
        # «leere Datei».
        groesse = None

    if groesse == 0:
        return _befund(
            brauchbar=False, format=None, groesse_byte=0,
            grund=f"{pfad.name} ist leer (0 Byte).",
            naechster_schritt="Beim Export ist vermutlich etwas schiefgegangen — noch "
                              "einmal ausgeben lassen.",
            hinweise=hinweise)

    if groesse is not None and groesse >= GROESSE_WARNSCHWELLE_BYTE:
        hinweise.append(
            f"Die Datei ist {groesse / 1e9:.1f} GB gross. Das geht, dauert aber: Auf "
            f"einem Laptop rechnet der Import dann in Minuten statt in Sekunden. "
            f"Gewarnt, nicht gesperrt — wer eine grosse Datei hat, hat sie.")

    anfang = _lies_anfang(pfad)

    # ── Können WIR es umwandeln? Diese Frage kommt vor der Absage ───────────────────
    #
    # Sonst weist die Tuer ab, was drinnen laengst geht. Die Reihenfolge ist der ganze
    # Unterschied: `_fremdes_format` kennt FBX als «koennen wir nicht» und haette den
    # Rat gegeben, sie doch selbst zu exportieren.
    eigene = _eigene_umwandlung(anfang, pfad.suffix.lower())
    if eigene is not None:
        # DIE ZUSAGE HAENGT AN EINER FREMDEN FASSUNG, und seit dem 21.09.2026 steht das
        # dabei: Blender 5.2.1 hat Collada und X3D ENTFERNT (gemessen, `auf-20260921-126`).
        # Wer hier «wird umgewandelt» liest und dann eine Fehlermeldung bekommt, ist
        # schlechter dran als jemand, der es von vornherein weiss.
        #
        #     *Ein Versprechen, das von einer fremden Fassung abhaengt, ist ohne diesen
        #     Zusatz keine Zusage, sondern eine Wette.*
        vorbehalt = FASSUNGSABHAENGIG.get(pfad.suffix.lower())
        hinweise.append(
            f"{eigene} wird beim Import umgewandelt — das kostet einen Programmstart und "
            f"geschieht von selbst."
            + (f" ACHTUNG: {vorbehalt}" if vorbehalt else ""))
        hinweise.append(
            "Ueber Einheit und Hochachse dieser Datei ist hier noch nichts bekannt: Der "
            "Kopf laesst sich nur bei IFC und glTF lesen. Was darin steht, zeigt sich "
            "erst nach der Umwandlung — und wird dann gemeldet, nicht stillschweigend "
            "zurechtgerueckt.")
        return _befund(
            brauchbar=True, format=eigene, groesse_byte=groesse,
            grund=f"Das ist {eigene}. Damit laesst sich rechnen — dieses Werkzeug wandelt "
                  f"die Datei beim Import selbst um.",
            naechster_schritt=None,
            hinweise=hinweise)

    # ── Format am INHALT, nicht an der Endung ────────────────────────────────────────
    fremd = _fremdes_format(anfang)
    if fremd is not None:
        name, rat = fremd
        return _befund(
            brauchbar=False, format=name, groesse_byte=groesse,
            grund=f"Das sieht aus wie {name}. Damit rechnet dieses Werkzeug nicht — "
                  f"es kann {', '.join(UNSERE_FORMATE)}.",
            naechster_schritt=rat,
            hinweise=hinweise)

    ist_ifc = b"ISO-10303-21" in anfang.upper()
    ist_gltf = anfang[:4] == b"glTF" or anfang.lstrip()[:1] == b"{"

    if not (ist_ifc or ist_gltf):
        # NICHT ENTSCHEIDBAR und ausdrücklich nicht «unbrauchbar»: Wir haben nichts
        # erkannt, und das ist eine Aussage über unsere Kennungen, nicht über die Datei.
        return _befund(
            brauchbar=None, format=None, groesse_byte=groesse,
            grund=f"Was in {pfad.name} steht, lässt sich nicht erkennen — es ist weder "
                  f"eine IFC noch eine glTF, und auch keines der Formate, die dieses "
                  f"Werkzeug beim Namen nennen kann.",
            naechster_schritt="Falls es ein Gebäudemodell ist: aus dem Programm, in dem "
                              "es entstand, als IFC oder als glTF (.glb) ausgeben.",
            hinweise=hinweise)

    # ── Der Kopf, über das Modul, das es schon kann ──────────────────────────────────
    try:
        kopf = herkunft.deute(pfad)
    except herkunft.HerkunftError as fehler:
        # Das Format ist erkannt, der Kopf aber nicht lesbar. Das ist ein Urteil über die
        # Datei (sie ist beschädigt) und darum ein Befund, keine Ausnahme.
        return _befund(
            brauchbar=False, format="IFC" if ist_ifc else "glTF", groesse_byte=groesse,
            grund=f"{pfad.name} fängt an wie eine {'IFC' if ist_ifc else 'glTF'}, aber "
                  f"ihr Kopf ist nicht lesbar: {fehler}",
            naechster_schritt="Die Datei ist vermutlich unvollständig übertragen oder "
                              "beim Export abgebrochen — noch einmal ausgeben lassen.",
            hinweise=hinweise)

    hinweise.extend(kopf.get("warnungen") or ())

    endung = pfad.suffix.lower().lstrip(".")
    erwartet = {"IFC": {"ifc"}, "glTF": {"glb", "gltf"}}.get(kopf.get("format"), set())
    endung_passt = None if not endung or not erwartet else endung in erwartet
    if endung_passt is False:
        hinweise.append(
            f"Die Datei heisst .{endung}, ist aber {kopf['format']}. Das stört hier "
            f"nicht — entschieden wird am Inhalt. Andere Werkzeuge glauben aber der "
            f"Endung, und dort fällt es dann auf.")

    steht_fest = kopf.get("sicherheit") in herkunft.SICHER and bool(kopf.get("up_axis"))
    if not steht_fest:
        hinweise.append(
            "Welche Achse oben ist, steht in dieser Datei nicht fest. Sie muss beim "
            "Rendern angegeben werden — wird sie falsch angegeben, liegt das Gebäude auf "
            "der Seite, und es fällt nirgends auf: Tiefenkarte, Kamera und Prüfung sind "
            "dann gemeinsam verdreht und darum in sich stimmig.")

    einheit = kopf.get("laengeneinheit")
    teile = [str(kopf.get("schema") or kopf.get("format"))]
    if einheit:
        teile.append(f"Längen in {einheit}")
    if kopf.get("erzeuger") or kopf.get("generator"):
        teile.append(f"erzeugt mit {kopf.get('erzeuger') or kopf.get('generator')}")

    return _befund(
        brauchbar=True, format=kopf.get("format"), groesse_byte=groesse,
        grund=", ".join(teile) + ". Damit lässt sich rechnen.",
        naechster_schritt=(
            "Der Lauf kann beginnen." if steht_fest else
            "Der Lauf kann beginnen, sobald die Hochachse angegeben ist."),
        hinweise=hinweise, endung_passt=endung_passt, kopf=kopf,
        hochachse=kopf.get("up_axis") if steht_fest else None,
        hochachse_steht_fest=steht_fest)


def _befund(*, brauchbar, format, grund, naechster_schritt, hinweise,
            groesse_byte=None, endung_passt=None, kopf=None,
            hochachse=None, hochachse_steht_fest=False) -> dict:
    """Ein Befund in **immer derselben Gestalt** — auch dort, wo wenig davon gefüllt ist.

    **Warum jedes Feld immer dasteht:** Ein Aufrufer, der ``befund["hinweise"]`` liest,
    darf nicht wissen müssen, welchen Weg die Prüfung genommen hat. Ein fehlender
    Schlüssel wäre ein ``KeyError`` mitten in einer Fehlerbehandlung — also genau dort, wo
    am wenigsten jemand damit rechnet.
    """
    return {
        "brauchbar": brauchbar,
        "grund": grund,
        "format": format,
        "endung_passt": endung_passt,
        "groesse_byte": groesse_byte,
        "hochachse": hochachse,
        "hochachse_steht_fest": bool(hochachse_steht_fest),
        "kopf": kopf,
        "hinweise": list(hinweise),
        "naechster_schritt": naechster_schritt,
    }
