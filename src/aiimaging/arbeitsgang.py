"""Der **Arbeitsgang** — hier kommen Import, Kette und Projekt zusammen.

Warum es diese Schicht gibt und warum sie dünn ist
--------------------------------------------------
Seit dem 21.09.2026 gibt es zwei neue Bausteine: :mod:`aiimaging.importeur` holt ein
Modell herein, :mod:`aiimaging.projekt` hält fest, was daraus wurde. Beide waren
**an keiner Stelle verdrahtet** — sie konnten etwas, und niemand rief sie.

    *Ein gebautes Modul ohne Aufrufer ist kein Werkzeug, sondern ein Vorrat.*

Dieses Modul ist der Aufrufer. Es ist die **einzige** Stelle, an der die drei zusammen
vorkommen, und es tut selbst nichts: Es wandelt nicht um, es rendert nicht, es misst
nicht. Es ruft in einer Reihenfolge, die begründbar ist, und schreibt danach auf, was
herauskam.

**Warum das eine eigene Datei ist und nicht eine Funktion in einem der drei.**
Käme sie in :mod:`aiimaging.projekt`, müsste das Projekt die Kette kennen — und damit
wäre die Mappe, in der die Arbeit liegt, an die Art gebunden, wie gerechnet wird. Käme
sie in :mod:`aiimaging.kette`, müsste die Kette wissen, wohin ihr Ergebnis gehört.
Beides sind Kopplungen, die man später nicht mehr auflöst.

Zwei Entscheide, die man beim Lesen sofort merkt
------------------------------------------------
**1 · Ein verändertes Modell hält den Lauf an — aber es lässt sich übergehen.**
:func:`rechne` weigert sich, wenn das Modell seit dem letzten Öffnen ein anderes geworden
oder verschwunden ist. Das ist **nicht** dasselbe wie die Regel «beim Öffnen wird nichts
repariert»: Öffnen ist harmlos, *Rechnen schreibt ein Urteil in die Mappe.* Ein Urteil,
das gegen ein anderes Gebäude gemessen wurde und unter dem alten Modellnamen steht, ist
schlimmer als gar keines.

Wer es trotzdem will — etwa, um zwei Stände zu vergleichen —, sagt ``trotz_aenderung=True``.
Dann läuft es, **und an jedem erzeugten Bild steht, unter welchem Modellstand es entstand.**

    *Ein Riegel, den man nicht aufmachen kann, wird umgangen. Einer, dessen Öffnen im
    Ergebnis steht, wird benutzt und bleibt sichtbar.*

**2 · Jedes erzeugte Bild wird vermerkt — auch das ohne Urteil.**
Das Urteil kommt aus dem QA-Knoten desselben Laufs; gibt es keinen, steht ``None`` da.
Nicht «nichts», sondern ``None`` mit Grund. Ein Bild ohne Eintrag wäre später von einem
Bild ohne Prüfung nicht zu unterscheiden — und beide sähen aus wie ein bestandenes.

Regel 4: Aufrufbar aus reinem Python. Die Ausführer der Kette lassen sich übergeben; ohne
GPU und ohne Blender läuft dieses Modul mit Attrappen vollständig durch.
"""
from __future__ import annotations

from pathlib import Path

from aiimaging import importeur, kette, projekt

__all__ = ["ArbeitsgangError", "lege_an", "rechne"]


class ArbeitsgangError(ValueError):
    """Der Ablauf kann so nicht laufen — und der Satz sagt, was fehlt.

    **Nicht** für einen schlechten Lauf: Eine Kette, die scheitert, liefert ein Ergebnis
    mit ``status`` und ``error``, und das wird vermerkt statt geworfen. Geworfen wird nur,
    was den Lauf gar nicht erst zulässt.
    """


def lege_an(wurzel, modell, *, name: str | None = None,
            einstellungen: dict | None = None, timeout: float | None = None,
            _starte=None) -> dict:
    """Ein Modell hereinholen **und** die Mappe dazu anlegen — in einem Griff.

    Args:
        wurzel: Der Projektordner.
        modell: Die Modelldatei in irgendeinem Format aus :data:`importeur.WEGE`.
        name: Anzeigename des Projekts.
        einstellungen: Was der Lauf später braucht (Backbone, Auflösung, Prompt …).
        timeout: Gesamtfrist für die Umwandlung.

    Returns:
        ``{projekt, import_bericht, pfad}``. Das Projekt ist **geschrieben**.

    Raises:
        ArbeitsgangError: Die Umwandlung selbst ist gescheitert (Blender fehlt, Subprozess
            ohne Bericht). Ein **abgelehntes** Modell ist kein Fehler — es steht als
            Befund im Projekt, samt dem Satz, was zu tun wäre.

    **Warum die glb neben der Projektdatei landet und das Quellmodell nicht.**
    Das Quellmodell bleibt, wo es ist (*eine Kopie wäre eine zweite Wahrheit*). Die daraus
    gerechnete glb ist dagegen ein **Erzeugnis dieses Projekts** und gehört hinein: Sie
    entsteht hier, sie ist hier reproduzierbar, und sie hat ausserhalb keinen Ort.
    """
    wurzel = Path(wurzel)
    p = projekt.neu(wurzel, modell, name=name, einstellungen=einstellungen)

    zusatz = {}
    if timeout is not None:
        zusatz["timeout"] = timeout
    bericht = importeur.importiere(modell, wurzel / "modell.glb",
                                   _starte=_starte, **zusatz)

    # DER IMPORTBERICHT GEHOERT INS PROJEKT, und zwar vollstaendig. Er sagt, ueber welchen
    # Weg das Modell hereinkam und was dabei NICHT geprueft wurde (`treue`). Spaeter ist
    # das nicht mehr zu rekonstruieren: Die glb allein sagt nicht, woraus sie entstand.
    # DIE HOCHACHSE — und hier entscheidet sich, ob wir sie WISSEN oder nur glauben.
    #
    # glTF kennt kein Feld dafuer, und die Erzeuger im Oekosystem sind sich uneinig. Ein
    # Vorgabewert waere eine stille Verdrehung: Tiefenkarte, Kamera und Pruefung kippen
    # dann GEMEINSAM und sind darum in sich stimmig. *Ein Fehlschlag, der wie ein Erfolg
    # aussieht, wird nicht gefunden — er wird geglaubt.*
    #
    # Es gibt genau zwei Faelle, und sie sind verschieden viel wert:
    #
    #   UMGEWANDELT (Weg `ifc` oder `blender`) — dann ist die glb UNSER Erzeugnis, und
    #       beide Wege schreiben Y-up. Das ist keine Annahme ueber eine fremde Datei,
    #       sondern eine Tatsache ueber unseren eigenen Lauf; der Bericht sagt sie.
    #
    #   DURCHGEREICHT — dann ist es eine fremde glb, und wir wissen NICHTS. Hier wird
    #       nicht geraten. Der Lauf verlangt die Angabe spaeter ausdruecklich.
    hochachse = bericht.get("bericht", {}).get("up_axis") if bericht["status"] == "ok" else None
    steht_fest = bool(hochachse) and bericht["weg"] != importeur.WEG_DURCHGEREICHT

    p["import"] = {
        "status": bericht["status"],
        "weg": bericht["weg"],
        "glb": bericht["glb_path"],
        "format": bericht["format"],
        "treue": bericht["treue"],
        "hochachse": hochachse if steht_fest else None,
        "hochachse_steht_fest": steht_fest,
        "hinweise": list(bericht.get("hinweise") or ()),
        "grund": bericht.get("grund"),
        "naechster_schritt": bericht.get("naechster_schritt"),
    }
    pfad = projekt.speichere(p, wurzel)
    return {"projekt": p, "import_bericht": bericht, "pfad": pfad}


def _urteil_zu(graph, knoten_ergebnisse: dict, bild_knoten: str):
    """Welches Urteil gehört zu diesem Bildknoten? ``(urteil, grund, qa_id)``.

    ``urteil`` ist ``True``, ``False`` oder ``None`` — und ``None`` heisst **nicht
    gemessen**, mit einem Grund daneben. Widersprechen sich zwei Prüfungen über dasselbe
    Bild, ist das Urteil ebenfalls ``None``: *Eines auszuwählen hiesse, das andere zu
    verschweigen.*
    """
    passende = [k for k in sorted(graph.knoten)
                if graph.knoten[k].art == kette.ART_QA
                and len(graph.knoten[k].eingaenge) >= 2
                and graph.knoten[k].eingaenge[1] == bild_knoten]
    if not passende:
        return None, ("Zu diesem Bild gibt es in diesem Lauf keine Geometrie-Prüfung. "
                      "NICHT GEMESSEN — weder bestanden noch durchgefallen."), None

    urteile = []
    for k in passende:
        eintrag = knoten_ergebnisse.get(k) or {}
        if eintrag.get("status") != kette.STATUS_OK:
            continue
        ausgaben = eintrag.get("ausgaben") or {}
        if "bestanden" in ausgaben:
            urteile.append((k, ausgaben["bestanden"], ausgaben.get("grund")))

    if not urteile:
        return None, (f"Die Prüfung {', '.join(passende)} hat in diesem Lauf kein Urteil "
                      f"geliefert (nicht gelaufen, übersprungen oder gescheitert). "
                      f"NICHT GEMESSEN."), None
    werte = {w for _, w, _ in urteile}
    if len(werte) > 1:
        return None, (f"Mehrere Prüfungen urteilen über dasselbe Bild und widersprechen "
                      f"sich ({', '.join(k for k, _, _ in urteile)}). Eines auszuwählen "
                      f"hiesse, das andere zu verschweigen."), None
    qa_id, urteil, grund = urteile[0]
    return urteil, grund, qa_id


def rechne(wurzel, *, trotz_aenderung: bool = False, ausfuehrer=None, cache=None,
           melder=None, **kettenargumente) -> dict:
    """Die Kette für ein Projekt fahren — **und jedes Bild samt Urteil eintragen.**

    Args:
        wurzel: Der Projektordner.
        trotz_aenderung: ``True`` lässt rechnen, obwohl das Modell ein anderes geworden
            oder verschwunden ist. Der Modellstand steht dann **an jedem erzeugten Bild**.
        ausfuehrer: Knotenart → Funktion, wie bei :func:`aiimaging.kette.fuehre_aus`.
            Ohne Angabe die echten — dann braucht es Blender, Gewichte und eine GPU.
        cache: Zwischenspeicher der Kette.
        melder: ``(ereignis: dict) -> None``, gerufen vor und nach jedem Knoten — und
            **zusätzlich nach jedem Diffusionsschritt** der Bildstufe. ``None`` heisst:
            niemand sieht zu.

            Die Schritte kommen als ``{"art": "schritt", "schritt": n}``. Sie sind der
            **einzige belegte Fortschritt** dieses Projekts: gezählt wird, was wirklich
            gerechnet wurde. Was ein Blender-Lauf meldet, ist dagegen ein *Lebens*zeichen
            und kein Fortschritt — die beiden dürfen in einer Anzeige nie gleich aussehen.

            **Der Zähler wird nur dann eingehängt, wenn kein eigener ``ausfuehrer``
            übergeben ist.** Wer die Tabelle selbst mitbringt, hat seine Gründe, und eine
            stille Ersetzung darin wäre genau die Sorte Überraschung, gegen die
            ``fuehre_aus`` die Tabelle ausdrücklich *ersetzen* statt ergänzen lässt.
        **kettenargumente: alles Weitere an :func:`aiimaging.kette.baue_kette` (Prompt,
            Seed, Auflösung …). Was im Projekt unter ``einstellungen`` steht, wird
            **vorangestellt** und hier überschrieben — *die Mappe trägt die Vorgabe, der
            Aufruf das Besondere.*

    Returns:
        ``{projekt, lauf, vermerkt, modell_stand, pfad}``. ``vermerkt`` ist die Zahl der
        eingetragenen Bilder. Das Projekt ist **geschrieben**.

    Raises:
        ArbeitsgangError: Kein Modell zum Rechnen, oder das Modell hat sich geändert und
            ``trotz_aenderung`` ist nicht gesetzt.

    **Warum ein Lauf, der scheitert, trotzdem eingetragen wird.** Ein gescheiterter Lauf
    ist eine Tatsache über dieses Projekt. Ihn wegzuwerfen hiesse, dass zwei Zustände
    gleich aussehen: «wurde nie versucht» und «wurde versucht und ging nicht».
    """
    wurzel = Path(wurzel)
    auf = projekt.oeffne(wurzel)
    p, stand = auf["projekt"], auf["modell_stand"]

    if stand in (projekt.MODELL_VERAENDERT, projekt.MODELL_FEHLT) and not trotz_aenderung:
        raise ArbeitsgangError(
            f"{auf['modell_grund']}\n"
            f"Gerechnet wird darum nicht: Ein Urteil, das gegen ein anderes Gebäude "
            f"gemessen wurde und unter dem alten Modellnamen in der Mappe steht, ist "
            f"schlimmer als gar keines. Wer es trotzdem will — etwa um zwei Stände zu "
            f"vergleichen —, ruft mit trotz_aenderung=True; dann steht an jedem Bild, "
            f"unter welchem Modellstand es entstand.")

    glb = (p.get("import") or {}).get("glb")
    if not glb:
        raise ArbeitsgangError(
            "In diesem Projekt liegt keine umgewandelte Geometrie. Es ist vermutlich "
            "nicht über `lege_an` entstanden, oder der Import wurde abgelehnt — der "
            "Grund steht dann unter 'import'.")

    # DIE MAPPE TRAEGT DIE VORGABE, DER AUFRUF DAS BESONDERE. Anders herum muesste man
    # jede Einstellung bei jedem Lauf wiederholen, und der erste vergessene Wert faellt
    # niemandem auf — er sieht aus wie eine Entscheidung.
    args = {**(p.get("einstellungen") or {}), **kettenargumente}
    args.pop("ifc_path", None)

    # DIE HOCHACHSE WIRD NICHT GERATEN, und das ist die einzige Stelle, an der dieses
    # Modul den Aufrufer wirklich um etwas bittet.
    if not args.get("up_axis"):
        einfuhr = p.get("import") or {}
        if einfuhr.get("hochachse_steht_fest"):
            args["up_axis"] = einfuhr["hochachse"]
        else:
            raise ArbeitsgangError(
                "Welche Achse oben ist, steht für dieses Modell nicht fest. Es kam als "
                "glTF herein, und glTF hat kein Feld dafür — die Erzeuger im Ökosystem "
                "sind sich uneinig.\n"
                "Geraten wird hier nicht: Eine falsche Angabe verdreht Tiefenkarte, "
                "Kamera und Prüfung GEMEINSAM. Das Ergebnis ist dann in sich stimmig und "
                "vollständig falsch, und es fällt nirgends auf.\n"
                "Angeben mit up_axis='Y' oder up_axis='Z'. Wer es nicht weiss: Eine IFC "
                "trägt die Angabe selbst — der Weg über IFC beantwortet die Frage, statt "
                "sie zu stellen.")

    graph = kette.baue_kette(glb_path=glb, **args)

    tabelle = ausfuehrer
    if melder is not None and ausfuehrer is None:
        tabelle = {**kette.AUSFUEHRER,
                   kette.ART_RENDER: kette.render_ausfuehrer(
                       schrittzaehler=lambda n: melder({"art": "schritt", "schritt": n}))}

    lauf = kette.fuehre_aus(graph, ausfuehrer=tabelle, cache=cache, melder=melder,
                            out_dir=str(wurzel / "laeufe"))
    knoten_ergebnisse = lauf.get("knoten") or {}
    schichten = kette.schichtbefund(graph, knoten_ergebnisse)

    vermerkt = 0
    for kid in sorted(graph.knoten):
        if not kette._ist_bildart(graph.knoten[kid].art):
            continue
        eintrag = knoten_ergebnisse.get(kid) or {}
        bild = (eintrag.get("ausgaben") or {}).get("bild_png")
        if not bild:
            # KEIN BILD, KEIN EINTRAG — und das ist kein Verschweigen: Ein Knoten ohne
            # Ausgabe hat nichts erzeugt, was in einer Bildliste stehen koennte. Dass er
            # lief und scheiterte, steht im Lauf, und der Lauf wird mitgeschrieben.
            continue

        urteil, grund, qa_id = _urteil_zu(graph, knoten_ergebnisse, kid)
        felder = schichten.get(kid) or {}
        projekt.vermerke_bild(
            p, bild=str(bild),
            schicht=felder.get(kette.FELD_SCHICHT, kette.SCHICHT_GEOMETRIE),
            urteil=urteil,
            basis=felder.get(kette.FELD_BASIS),
            herkunft={
                "knoten": kid,
                "grund": grund,
                "urteil_von": qa_id,
                "backbone": args.get("backbone"),
                "prompt": args.get("prompt"),
                "seed": args.get("seed"),
                # DER MODELLSTAND GEHOERT AN JEDES BILD, nicht nur in den Lauf. Wer
                # spaeter ein einzelnes Bild ansieht, sieht sonst nicht, dass es gegen
                # ein inzwischen geaendertes Modell gerechnet wurde.
                "modell_stand": stand,
            })
        vermerkt += 1

    p.setdefault("laeufe", []).append({
        "status": lauf.get("status"),
        "gerechnet": lauf.get("gerechnet"),
        "cache_treffer": lauf.get("cache_treffer"),
        "gescheitert": lauf.get("gescheitert"),
        "dauer_s": lauf.get("dauer_s"),
        "error": lauf.get("error"),
        "modell_stand": stand,
        "bilder_vermerkt": vermerkt,
    })
    pfad = projekt.speichere(p, wurzel)
    return {"projekt": p, "lauf": lauf, "vermerkt": vermerkt,
            "modell_stand": stand, "pfad": pfad}
