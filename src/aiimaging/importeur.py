"""Schritt 1 — **das 3D-Modell kommt herein.** Ein Aufruf, beliebig viele Formate.

Der Auftrag, und warum er der erste ist
---------------------------------------
Diese Software soll eine Architektin herunterladen, ihr Modell hineinziehen und ein Bild
bekommen. Der erste Schritt ist damit nicht das Rendern, sondern der **Import** — und er
entscheidet, ob es überhaupt einen zweiten gibt.

Stand bis zum 21.09.2026: Das Projekt kannte **drei** Formate — ``glb``, ``gltf``,
``ifc``. Alles andere lief gegen eine Absage mit einem Rat, zum Beispiel: *«Blender liest
FBX und schreibt glTF: Datei → Exportieren → glTF 2.0.»*

Der Rat ist sachlich richtig, und er ist eine Zumutung. Er verlangt von jemandem, der
Bilder machen will, dass er zuerst ein Programm installiert und bedient, **das diese
Software selbst schon aufruft** — Blender steht seit August als Subprozess hinter der
Multipass-Stufe.

    *Ein Werkzeug, das den Weg kennt und ihn dem Benutzer aufträgt, hat die Arbeit nicht
    getan, sondern verteilt.*

Die drei Wege, und warum es drei sind und nicht einer
-----------------------------------------------------
======================  ================================================================
:data:`WEG_DURCHGEREICHT`  ``glb``/``gltf`` — das Zielformat selbst. Es wird **nicht**
                           durch Blender geschickt, obwohl Blender es lesen könnte: Jede
                           Umwandlung kann etwas verlieren, und eine Umwandlung ohne
                           Zweck kann nur verlieren.
:data:`WEG_IFC`            ``ifc`` — über :func:`aiimaging.seams.ifc_zu_glb` und das
                           ``.venv-ifc``. IfcOpenShell ist LGPL und bleibt hinter seiner
                           eigenen Prozessgrenze (Regel 1).
:data:`WEG_BLENDER`        alles Übrige — ``obj``, ``fbx``, ``dae``, ``stl``, ``ply``,
                           ``usd``, ``abc``, ``x3d``. Über
                           ``blender --background --python`` (Regel 2).
======================  ================================================================

**IFC geht nicht über Blender, obwohl Blender IFC lesen kann.** Der Weg dorthin hiesse
BlenderBIM, und BlenderBIM ist GPL — als Add-on im Produktprozess wäre das genau die
Verbindung, die Regel 2 ausschliesst. Der eigene IFC-Weg ist darum kein Umweg, sondern
die Bedingung dafür, dass diese Software permissiv bleiben darf.

Was dieses Modul ausdrücklich NICHT tut
---------------------------------------
* **Es repariert nichts.** Falsche Einheit, gekippte Achse, Modell im Nullpunkt-Abseits:
  gemeldet, nicht behoben. *Ein stillschweigend behobener Fehler wandert unbemerkt durch
  die ganze Kette und taucht am Ende als unerklärliche Zahl wieder auf.*
* **Es prüft die Umwandlung nicht von selbst.** Ob aus den Dreiecken das Gebäude wurde,
  das in der Datei stand, kann niemand wissen, der die Wahrheit nicht kennt. Wer sie
  kennt, übergibt sie als ``erwartung`` — dann läuft
  :func:`aiimaging.konversionstreue.pruefe_konversion` mit, und das Ergebnis steht im
  Bericht. Ohne ``erwartung`` steht dort ``treue: None``, und ``None`` heisst hier
  **nicht geprüft**, nicht «in Ordnung».
* **Es entscheidet nicht über die Hochachse.** Es reicht weiter, was
  :mod:`aiimaging.einlass` darüber sagt, samt der Angabe, ob sie feststeht.

Regel 4: Alles hier ist aus reinem Python aufrufbar, ohne Oberfläche.
"""
from __future__ import annotations

import json
from pathlib import Path

from aiimaging import einlass, konversionstreue, seams

__all__ = [
    "FORMATE_BLENDER", "ImporteurError", "WEGE", "WEG_BLENDER", "WEG_DURCHGEREICHT",
    "WEG_IFC", "importiere", "kann_importieren", "weg_fuer_endung",
]


class ImporteurError(ValueError):
    """Der Import **selbst** ist gescheitert — nicht die Datei.

    Derselbe Unterschied wie bei :class:`aiimaging.einlass.EinlassError`: Eine
    unbrauchbare Datei ist ein *Befund* und kommt als Bericht mit ``status: "abgelehnt"``
    zurück. Ein fehlendes Blender, ein unlesbares Verzeichnis, ein abgestürzter
    Subprozess sind *Fehler des Werkzeugs* und fliegen.

    Wer beides zusammenwirft, kann später nicht mehr unterscheiden, ob die Datei schlecht
    war oder die Einrichtung.
    """


#: Das Zielformat kommt unverändert durch.
WEG_DURCHGEREICHT = "durchgereicht"
#: Über das ``.venv-ifc`` und IfcOpenShell.
WEG_IFC = "ifc"
#: Über einen Blender-Subprozess.
WEG_BLENDER = "blender"

#: Endung → Anzeigename, für alles, was über Blender hereinkommt.
#:
#: **Gleichlautend mit** ``runners/blender_import_runner.IMPORTEURE``, und das ist eine
#: bewusste Doppelung: Der Runner darf aus dem Produkt nicht importiert werden (er braucht
#: ``bpy``), also kann diese Seite seine Tabelle nicht lesen. ``tests/test_importeur.py``
#: hält die beiden deckungsgleich — *eine Doppelung ohne Wächter wird zur Abweichung.*
FORMATE_BLENDER: dict[str, str] = {
    ".obj": "Wavefront OBJ",
    ".fbx": "Autodesk FBX",
    ".dae": "Collada",
    ".stl": "STL",
    ".ply": "Stanford PLY",
    ".usd": "USD",
    ".usdc": "USD (binär)",
    ".usda": "USD (Text)",
    ".abc": "Alembic",
    ".x3d": "X3D",
}

#: Endung → Weg. Die einzige Stelle, an der entschieden wird, wohin eine Datei geht.
WEGE: dict[str, str] = {
    ".glb": WEG_DURCHGEREICHT,
    ".gltf": WEG_DURCHGEREICHT,
    ".ifc": WEG_IFC,
    **{endung: WEG_BLENDER for endung in FORMATE_BLENDER},
}

#: Wie lange ein Blender-Import höchstens dauern darf.
#:
#: **GESETZT, nicht gemessen** — und das steht hier, weil es sonst niemand wüsste. Der
#: Wert ist derselbe wie bei den IFC-Läufen (300 s), aus demselben Grund: Ein Import
#: schreibt seinen Bericht erst am Ende, es wächst währenddessen nichts nachweislich, und
#: die Gesamtfrist ist darum der einzige Riegel. Auf einer langsamen Maschine ist der Weg
#: ``AIIMAGING_ZEITFAKTOR``, nicht ``None``.
GESAMTFRIST_BLENDER_S = 300


def weg_fuer_endung(endung: str) -> str | None:
    """Welcher Weg gilt für diese Endung — oder ``None``, wenn wir sie nicht können.

    ``None`` heisst **nicht** «kaputte Datei». Es heisst, dass dieses Projekt für dieses
    Format keinen Weg hat, und das ist eine Aussage über uns, nicht über die Datei.
    """
    return WEGE.get(str(endung).lower())


def kann_importieren(endung: str) -> bool:
    """Gibt es für diese Endung einen Weg? Die kurze Form von :func:`weg_fuer_endung`."""
    return weg_fuer_endung(endung) is not None


def _ablehnung(befund: dict, quelle: Path, grund: str, naechster_schritt: str) -> dict:
    """Ein Bericht, der sagt: nein — **und wie es doch gehen könnte.**

    *Eine Absage ohne Ausweg ist eine halbe Auskunft.* Jede Ablehnung hier trägt darum
    ``naechster_schritt``, und der ist ein Satz in der Sprache dessen, der die Datei hat,
    nicht in der des Programms.
    """
    return {
        "status": "abgelehnt",
        "glb_path": None,
        "weg": None,
        "quelle": quelle.name,
        "format": befund.get("format") if befund else None,
        "grund": grund,
        "naechster_schritt": naechster_schritt,
        "hochachse": befund.get("hochachse") if befund else None,
        "hochachse_steht_fest": befund.get("hochachse_steht_fest") if befund else None,
        "treue": None,
        "hinweise": list(befund.get("hinweise") or []) if befund else [],
        "bericht": None,
        "error": None,
    }


def _erfolg(*, glb: Path, weg: str, quelle: Path, befund: dict | None,
            bericht: dict, hinweise: list[str], treue: dict | None) -> dict:
    return {
        "status": "ok",
        "glb_path": str(glb),
        "weg": weg,
        "quelle": quelle.name,
        "format": (befund or {}).get("format"),
        "grund": None,
        "naechster_schritt": None,
        "hochachse": (befund or {}).get("hochachse"),
        "hochachse_steht_fest": (befund or {}).get("hochachse_steht_fest"),
        # NICHT GEPRUEFT IST NICHT IN ORDNUNG. Ohne `erwartung` weiss niemand, ob aus der
        # Datei das wurde, was darin stand — und `None` sagt genau das. Ein `True` an
        # dieser Stelle waere die teuerste Luege des ganzen Moduls: Sie wuerde eine
        # verdrehte Geometrie durch die ganze Kette tragen und am Ende als schlechte
        # Bildqualitaet erscheinen.
        "treue": treue,
        "hinweise": hinweise,
        "bericht": bericht,
        "error": None,
    }


def _sichte(quelle: Path) -> dict | None:
    """Der Sichtgang, und ein gescheiterter Sichtgang hält hier nichts auf.

    Anders als bei :func:`aiimaging.seams.ifc_zu_glb` **darf** hier abgewiesen werden:
    Das ist ein neuer Weg und kein laufender, und ein Tor, das nichts sperrt, was gestern
    lief, kostet niemanden etwas. Kommt der Sichtgang selbst nicht durch (Rechte,
    Netzlaufwerk), gilt weiter die Endung — *ein Wächter, der den Betrieb anhält, weil er
    selbst nicht laufen kann, ist schlimmer als keiner.*
    """
    try:
        return einlass.sichte(quelle)
    except einlass.EinlassError:
        return None


def _blender_import(quelle: Path, ziel: Path, *, timeout: float, starte) -> dict:
    """Der Subprozess-Aufruf. Wirft :class:`ImporteurError`, wenn das Werkzeug fehlt."""
    blender = seams.finde_blender()
    runner = Path(seams.__file__).parent / "runners" / "blender_import_runner.py"
    bericht_datei = ziel.parent / f"{ziel.stem}_import.json"
    ziel.parent.mkdir(parents=True, exist_ok=True)

    cmd = [blender, "--background", "--factory-startup", "--python", str(runner), "--",
           "--quelle", str(quelle), "--glb", str(ziel), "--report", str(bericht_datei)]
    ergebnis = starte(cmd, int(timeout))

    # DER BERICHT ZUERST, DER RUECKGABEWERT DANACH — und die Reihenfolge ist ein Entscheid.
    #
    # Blender gibt auf manchen Maschinen auch bei gelungenem Lauf einen Code ungleich null
    # zurueck (Treiberwarnungen beim Beenden). Wer zuerst den Code liest, wirft einen
    # gelungenen Import weg. Wer zuerst den Bericht liest, hat die Auskunft aus erster
    # Hand — und faellt nur dann auf den Code zurueck, wenn gar kein Bericht da ist.
    if bericht_datei.exists():
        try:
            bericht = json.loads(bericht_datei.read_text(encoding="utf-8"))
        except (OSError, ValueError) as fehler:
            raise ImporteurError(
                f"Der Import-Bericht liess sich nicht lesen ({fehler}). Das ist ein "
                f"Fehler der Einrichtung, nicht der Datei.") from fehler
        if bericht.get("status") == "ok":
            return bericht
        raise ImporteurError(
            f"Blender konnte {quelle.name} nicht lesen: {bericht.get('error')}")

    hinweis = (ergebnis.stderr or ergebnis.stdout or "").strip()
    raise ImporteurError(
        f"Der Blender-Lauf hat keinen Bericht geschrieben (Rückgabewert "
        f"{ergebnis.returncode}). {hinweis[:400]}")


def importiere(quelle, ziel_glb, *, erwartung: dict | None = None,
               timeout: float = GESAMTFRIST_BLENDER_S, _starte=None) -> dict:
    """Ein 3D-Modell hereinholen — **ein Aufruf für alle Formate, die wir können.**

    Args:
        quelle: Die Modelldatei, in irgendeinem der Formate aus :data:`WEGE`.
        ziel_glb: Wohin die glb geschrieben wird. Beim Weg
            :data:`WEG_DURCHGEREICHT` wird **nichts geschrieben** und ``glb_path`` zeigt
            auf die Quelle selbst — eine Kopie wäre eine zweite Wahrheit auf der Platte.
        erwartung: Die bekannte Wahrheit über das Modell, falls es eine gibt:
            ``{"huellbox_m": (x, y, z), "n_bauteile": int|None, "n_dreiecke": int|None}``.
            Nur dann wird die Umwandlung nachgeprüft. Bei einer echten Datei kennt
            niemand diese Zahlen — *man müsste sie mit demselben Werkzeug ausrechnen, das
            man prüfen will.*
        timeout: Gesamtfrist des Subprozesses in Sekunden.

    Returns:
        Ein Bericht mit ``status`` (``"ok"`` oder ``"abgelehnt"``), ``glb_path``, ``weg``,
        ``format``, ``hochachse``, ``hochachse_steht_fest``, ``treue``, ``hinweise`` und
        dem rohen ``bericht`` des jeweiligen Wegs.

        **``status: "abgelehnt"`` ist kein Fehler**, sondern eine Auskunft: Die Datei
        kommt hier nicht durch, ``grund`` sagt warum und ``naechster_schritt`` sagt, was
        zu tun wäre.

    Raises:
        ImporteurError: Das Werkzeug fehlt oder der Lauf ist gescheitert — Blender nicht
            gefunden, ``.venv-ifc`` nicht da, Subprozess ohne Bericht.
    """
    quelle = Path(quelle)
    ziel = Path(ziel_glb)
    starte = _starte or seams._default_starte

    befund = _sichte(quelle)

    if not quelle.exists():
        return _ablehnung(befund or {}, quelle,
                          "Diese Datei gibt es nicht.",
                          "Pfad prüfen — Tippfehler, oder die Datei liegt woanders.")

    # DER SICHTGANG SCHLAEGT VOR DER ENDUNG ZU, und nicht umgekehrt.
    #
    # Eine JPG mit dem Namen `modell.glb` hat eine Endung, die wir koennen, und einen
    # Inhalt, den wir nicht koennen. Wer die Endung zuerst fragt, schickt sie in den
    # Subprozess und bekommt einen Fehler aus einer fremden Bibliothek zurueck.
    if befund is not None and befund["brauchbar"] is False:
        return _ablehnung(befund, quelle, befund["grund"], befund["naechster_schritt"])

    endung = quelle.suffix.lower()
    weg = weg_fuer_endung(endung)
    if weg is None:
        return _ablehnung(
            befund or {}, quelle,
            f"Für {endung or 'eine Datei ohne Endung'} hat dieses Programm keinen Weg.",
            "Die meisten CAD-Programme können glTF 2.0 (.glb) oder IFC ausgeben — beides "
            "kommt hier direkt herein.")

    hinweise = list((befund or {}).get("hinweise") or [])

    if weg == WEG_DURCHGEREICHT:
        # NICHTS TUN IST HIER DIE ARBEIT. Eine glb durch Blender zu schicken, um eine glb
        # zu bekommen, kann nur verlieren: Materialien, Namen, Hierarchie. Der Bericht
        # sagt darum ausdruecklich, dass nichts umgewandelt wurde — sonst sieht ein
        # Durchreichen spaeter aus wie eine gelungene Konversion.
        bericht = {"status": "ok", "glb_path": str(quelle), "umgewandelt": False,
                   "note": "Zielformat — nichts umgewandelt, nichts kopiert."}
        return _erfolg(glb=quelle, weg=weg, quelle=quelle, befund=befund,
                       bericht=bericht, hinweise=hinweise, treue=None)

    if weg == WEG_IFC:
        # `_starte` wird unveraendert durchgereicht, auch als `None`: `ifc_zu_glb` setzt
        # dann selbst seinen Vorgabeweg ein. Hier eine zweite Vorgabe zu treffen hiesse,
        # dieselbe Entscheidung an zwei Stellen zu haben.
        bericht = seams.ifc_zu_glb(quelle, ziel, timeout=timeout, _starte=_starte)
    else:
        bericht = _blender_import(quelle, ziel, timeout=timeout, starte=starte)
        hinweise += list(bericht.get("warnungen") or [])

    treue = None
    if erwartung is not None:
        treue = konversionstreue.pruefe_konversion(
            bericht,
            huellbox_m=erwartung["huellbox_m"],
            n_bauteile=erwartung.get("n_bauteile"),
            n_dreiecke=erwartung.get("n_dreiecke"))

    return _erfolg(glb=ziel, weg=weg, quelle=quelle, befund=befund,
                   bericht=bericht, hinweise=hinweise, treue=treue)
