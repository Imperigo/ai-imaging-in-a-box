"""HOCHACHSE — welche Achse oben ist, aus der Geometrie gemessen statt geglaubt.

Warum dieses Modul existiert
----------------------------
:func:`aiimaging.contracts.normalize_up_axis` ist am 19.09.2026 verschärft worden: Sie
fängt seither den **Tippfehler** — ``"Zeichnung"`` galt bis dahin als ``Z`` und drehte
das Gebäude. Sie fängt **den Irrtum nicht**: Wer ``"Z"`` schreibt, während das Modell
Y-up ist, bekommt dort kein Wort, denn die Angabe ist syntaktisch tadellos.

Und das ist die teuerste Stelle der ganzen Kette. Tiefenkarte, Kameraableitung und
Geometrie-QA werden nach einer falschen Achsenangabe **gemeinsam** verdreht und sind
darum *in sich stimmig*. Der Fehlschlag sieht wie ein Erfolg aus — und solche Fehler
werden nicht gefunden, sie werden geglaubt.

Die Vermutung, auf der alles hier steht
---------------------------------------
**Gelände ist in der Hochachse flach.** Eine Geländeplatte ist gross in den beiden
waagrechten Achsen und dünn in der senkrechten; welche Achse oben ist, liesse sich
daran *messen*.

:mod:`aiimaging.gelaendeform` beurteilt genau das — gross im Grundriss, flach, unten —
und nimmt die Höhenachse bereits als Parameter ``hoch`` entgegen. Dieses Modul stellt
ihr darum dieselbe Frage **dreimal**, einmal je Achse, und sieht nach, welche Achse
antwortet. Es setzt **keine eigene Formschwelle**: Die drei Zahlen, an denen ein Körper
als Platte gilt, stehen an ihrer einen Stelle in :mod:`aiimaging.gelaendeform`. *Eine
Regel an zwei Stellen ist an einer davon bereits falsch.*

Was gemessen ist — und was die Vermutung nicht trägt
----------------------------------------------------
Alle Zahlen unten sind an synthetischer Geometrie gemessen (19.09.2026,
``tests/test_hochachse.py``; Regel 3 — echte Modelle gibt es hier nicht):

===========================================  ============================================
Fall                                          Ergebnis
===========================================  ============================================
flache Platte 40×30×0,5 + Haus, Y-up          ``"Y"``, eindeutig — nur Y trägt einen Befund
dasselbe, Z-up                                ``"Z"``, eindeutig
zwei Baukörper, kein Gelände                  ``None`` — in keiner Achse eine Platte
Turm 10×40×10 allein                          ``None`` — **nicht** «die grösste Achse»
Hang, 4,0 m Anstieg auf 40 m                  ``"Y"`` — noch flach genug
Hang, 4,1 m Anstieg auf 40 m                  ``None`` — Flachheit über 0,15

*Nachgemessen am 19.09.2026 in Schritten von 0,1 m:* Die Grenze liegt zwischen **4,0 und
4,1 m**, nicht zwischen 4,0 und 4,2 — die erste Messung war in Schritten von 0,2 m
gefahren und nannte darum die nächstgrössere Stufe. Der Unterschied ändert nichts an der
Sache und steht hier trotzdem: *Eine Grenze, die feiner gemessen woanders liegt, war
vorher nicht gemessen, sondern eingegrenzt.*
gekacheltes Gelände (20 Stück)                ``None`` ohne, ``"Y"`` mit Familienprüfung
===========================================  ============================================

**Und hier trägt sie nicht** — der wichtigste Satz dieses Moduls:

    Eine grosse dünne Platte ist geometrisch dasselbe, ob sie liegt oder steht. Eine
    Fassade, die den Grundriss der Szene aufspannt und am Rand der Szene sitzt, ist in
    ihrer dünnen Achse «gross, flach und unten» — und diese Achse ist waagrecht.

Gemessen an einer Szene aus Fassadenplatte 16×15×0,3 und Haus 12×15×9, ohne Gelände,
Y-up: Die Messung antwortet **``"Z"``, eindeutig** — und sie irrt. Der Fall steht als
Test im Repo (``test_eine_stehende_platte_fuehrt_die_messung_in_die_irre``), damit er
nicht als Überraschung wiederkommt.

*Es gibt dagegen kein billiges Mittel.* Zwei Körper geben nicht genug her, um eine
liegende von einer stehenden Platte zu trennen; nur der Zusammenhang mit vielen weiteren
Körpern täte das. Was in derselben Messung auffiel und den Befund einordnet: **Sobald die
Szene ein echtes Gelände enthält, verschwindet der falsche Kandidat von selbst** — die
Platte dehnt die Szene in der waagrechten Achse, die Fassade rutscht aus dem unteren
Drittel und wird ``nicht entscheidbar``. Die Irreführung braucht also eine Szene *ohne*
Gelände, und in der ist die Antwort ohnehin unverdient.

Darum gilt für dieses Modul:

* Es ist eine **Gegenprobe**, kein Tor. Nichts ist damit verdrahtet, und der Einbau ist
  nicht entschieden — eine Gegenprobe, die zum Tor wird, bevor sie an echten Modellen
  gemessen ist, wäre derselbe Fehler noch einmal.
* :func:`gegenprobe` meldet bei Abweichung einen **Widerspruch**, nicht ein Urteil über
  die Angabe: Welche der beiden Seiten irrt, sagt sie ausdrücklich nicht.

``None`` heisst NICHT ENTSCHEIDBAR
----------------------------------
Weder Ja noch Nein. ``achse is None`` heisst: *hier wurde nichts gemessen.* Ein ``None``,
das still zu ``0`` oder ``False`` wird, ist an dieser Stelle der schwerste denkbare
Fehler — es machte aus «nicht geprüft» ein «geprüft und in Ordnung». Dasselbe gilt für
``gegenprobe(...)["stimmt"]``: ``None`` ist **nicht** ``False``.

Abhängigkeiten: keine. Reine stdlib, kein ``bpy`` (Regel 2), aus Python heraus ohne jede
Oberfläche aufrufbar (Regel 4).
"""
from __future__ import annotations

from . import gelaendeform as _gf
from .contracts import ContractError, normalize_up_axis
from .glbbox import knotenboxen, lies_gltf_json

#: Die drei Achsen der Datei, in der Reihenfolge der Koordinaten.
#:
#: **X wird mitgemessen, obwohl der Vertrag es nie zulässt**, und das ist Absicht: Eine
#: Messung, die nur zwischen Y und Z wählen darf, muss sich für eine der beiden
#: entscheiden, auch wenn keine passt. Gewinnt X, ist das ein Befund über die Datei
#: (dritte Konvention) oder über die Messung (eine stehende Platte) — und in beiden
#: Fällen die Antwort ``None`` mit Grund, nicht die zweitbeste Achse.
ACHSEN = ("X", "Y", "Z")

#: Die Achsen, die :func:`aiimaging.contracts.normalize_up_axis` kennt.
VERTRAGSACHSEN = ("Y", "Z")

#: Um welchen Faktor der Geländebefund der Siegerachse den der zweitbesten übertreffen
#: muss, damit überhaupt entschieden wird.
#:
#: **DIESE ZAHL IST GESETZT UND NICHT GEMESSEN.** Es gibt keine Messreihe, aus der sie
#: folgt; sie ist die Übersetzung einer Entscheidung in eine Zahl, und die Entscheidung
#: lautet: *Zwei Achsen mit einem Geländebefund ergeben keine Antwort.*
#:
#: Warum gerade 4,0 das leistet: Die Stärke einer Achse ist ein **Flächenanteil** in
#: ``[0, 1]`` (siehe :func:`_staerke`), und ein Befund entsteht nach
#: :data:`aiimaging.gelaendeform.GRUNDRISSANTEIL_MIN` erst ab 0,25. Eine zweitbeste Achse
#: mit Befund liegt also immer bei mindestens 0,25, und ``1,0 / 0,25 = 4,0``. Die
#: Schwelle sagt damit genau das Gewollte, und sie sagt es an der Obergrenze: Selbst der
#: stärkstmögliche Sieger kommt am schwächstmöglichen Zweiten nicht vorbei.
#:
#: **Woran sie kippt:** Sie hängt an ``GRUNDRISSANTEIL_MIN``. Sinkt diese Schwelle dort
#: — etwa weil ein Bestand kleinteiliges Gelände liefert —, wird 4,0 durchlässig und
#: entscheidet plötzlich zwischen zwei Achsen, die beide einen Befund tragen. Wer dort
#: nachzieht, zieht hier nach. Und sie kippt ein zweites Mal, sobald jemand eine Szene
#: misst, in der zwei Achsen *zu Recht* verschieden stark antworten; dann ist nicht die
#: Zahl falsch, sondern die Annahme, dass es so etwas nicht gibt.
VORSPRUNG_MIN = 4.0

#: Kurzschlüssel für :func:`hochachse_aus_knoten` — warum entschieden wurde oder nicht.
GEMESSEN = "gemessen"
KEINE_KNOTEN = "keine_knoten"
OHNE_GRENZEN = "ohne_grenzen"
KEINE_AUSDEHNUNG = "keine_ausdehnung"
KEIN_GELAENDE = "kein_gelaende"
MEHRDEUTIG = "mehrdeutig"
AUSSERHALB_DES_VERTRAGS = "achse_ausserhalb_des_vertrags"


def _huellknoten(alle, namen):
    """Die Hüllbox über die als Gelände erkannten Körper — als Knoten ``(name, lo, hi)``.

    Gemessen wird die Stärke einer Achse an der **Hülle** und nicht an der Summe der
    Einzelbefunde: Zwanzig Kacheln, die zusammen eine Platte bilden, sind eine Platte und
    nicht zwanzig. Die Summe ihrer Anteile ginge über 1,0 hinaus und wäre kein Anteil mehr.
    """
    teile = [k for k in alle if str(k[0]) in namen]
    if not teile:
        return None
    lo = [min(float(k[1][i]) for k in teile) for i in range(3)]
    hi = [max(float(k[2][i]) for k in teile) for i in range(3)]
    return ("gelaende-huelle", lo, hi)


def _staerke(alle, namen, hoch):
    """Wie stark eine Achse antwortet: der Grundrissanteil der Geländehülle, ``[0, 1]``.

    ``(0.0, None)``, wenn in dieser Achse kein Körper als Gelände gilt — **keine
    Stärke ist null, nicht «nicht gemessen»**: Die Frage wurde gestellt und mit Nein
    beantwortet.
    """
    huelle = _huellknoten(alle, set(namen))
    if huelle is None:
        return 0.0, None
    m = _gf.merkmale(huelle, alle, hoch=hoch)
    return float(m["grundrissanteil"]), m


def hochachse_aus_knoten(alle, *, als_familie: bool = True) -> dict:
    """Welche Achse ist oben? Gemessen an den Hüllboxen einer Szene.

    Args:
        alle: Knoten als ``(name, lo, hi)`` wie aus
            :func:`aiimaging.glbbox.knotenboxen` — in **Dateikoordinaten**, also vor
            jeder Umrechnung nach Welt. Eine bereits gedrehte Box zu messen hiesse, die
            Antwort vorauszusetzen.
        als_familie: Ob eine Namensfamilie gemeinsam beurteilt wird
            (:func:`aiimaging.gelaendeform.gelaende_knoten`). **Hier Vorgabe an**, und
            das weicht bewusst von dort ab: Dort ist sie aus, weil sie ändert, *was als
            Gelände gilt*, und daran hängt die Bauwerksmaske. Hier hängt nichts daran —
            gefragt wird allein nach der Achse, und ein Gelände, das als zwanzig Kacheln
            geliefert wird, ist sonst gar nicht zu sehen (gemessen: ohne
            Familienprüfung ``None``, mit ihr ``"Y"``).

    Returns:
        dict mit

        * ``achse`` — ``"Y"``, ``"Z"`` oder ``None``. **``None`` heisst NICHT
          ENTSCHEIDBAR**, weder Ja noch Nein.
        * ``grund`` — Kurzschlüssel (:data:`GEMESSEN`, :data:`KEIN_GELAENDE`,
          :data:`MEHRDEUTIG`, :data:`AUSSERHALB_DES_VERTRAGS`, …).
        * ``satz`` — ein Satz für einen Menschen, warum.
        * ``staerke`` / ``vorsprung`` — woran es festgemacht ist. ``vorsprung`` ist
          ``None``, wenn keine zweite Achse antwortete: Ein Verhältnis zu null gibt es
          nicht, und ``inf`` sähe wie eine Zahl aus.
        * ``sicherheit`` — ``"eindeutig"`` (keine zweite Achse antwortete),
          ``"knapp"`` (eine antwortete, blieb aber unter dem Vorsprung) oder ``None``.
        * ``achsen`` — je Achse die Zahlen, nicht nur das Urteil.
        * ``entschieden_durch_familie`` — ob die Familienprüfung den Ausschlag gab.
    """
    alle = list(alle)
    ergebnis = {
        "achse": None, "achse_index": None, "sicherheit": None,
        "grund": KEINE_KNOTEN, "satz": "", "staerke": None, "vorsprung": None,
        "achsen": {}, "n_knoten": len(alle), "als_familie": bool(als_familie),
        "entschieden_durch_familie": False,
    }
    if not alle:
        ergebnis["satz"] = (
            "NICHT ENTSCHEIDBAR: Die Szene traegt keinen einzigen Koerper. Ueber eine "
            "leere Szene sagt keine Form, welche Achse oben ist.")
        return ergebnis

    je_achse = {}
    for index, buchstabe in enumerate(ACHSEN):
        try:
            befund = _gf.gelaende_knoten(alle, hoch=index, als_familie=als_familie)
            einzeln = (_gf.gelaende_knoten(alle, hoch=index, als_familie=False)
                       if als_familie else befund)
            staerke, merkmale = _staerke(alle, befund["gelaende"], index)
        except _gf.GelaendeformError as e:
            # KEINE AUSKUNFT IST BESSER ALS EINE GERATENE. Eine Szene ohne Ausdehnung in
            # einer Achse macht jeden Anteil beliebig — und beliebig saehe wie gemessen aus.
            ergebnis["grund"] = KEINE_AUSDEHNUNG
            ergebnis["satz"] = (
                f"NICHT ENTSCHEIDBAR: Die Szene hat in mindestens einer Achse keine "
                f"Ausdehnung, ein Anteil daran waere beliebig. ({e})")
            return ergebnis
        je_achse[buchstabe] = {
            "n_gelaende": len(befund["gelaende"]),
            "n_gelaende_einzeln": len(einzeln["gelaende"]),
            "n_unklar": len(befund["unklar"]),
            "staerke": staerke,
            "gelaende_namen": tuple(befund["gelaende"])[:20],
            "grundrissanteil": None if merkmale is None else merkmale["grundrissanteil"],
            "flachheit": None if merkmale is None else merkmale["flachheit"],
            "tieflage": None if merkmale is None else merkmale["tieflage"],
        }
    ergebnis["achsen"] = je_achse

    rang = sorted(ACHSEN, key=lambda b: je_achse[b]["staerke"], reverse=True)
    beste, zweite = rang[0], rang[1]
    s_beste = je_achse[beste]["staerke"]
    s_zweite = je_achse[zweite]["staerke"]
    ergebnis["staerke"] = s_beste

    if s_beste <= 0.0:
        ergebnis["grund"] = KEIN_GELAENDE
        unklar = sum(je_achse[b]["n_unklar"] for b in ACHSEN)
        ergebnis["satz"] = (
            "NICHT ENTSCHEIDBAR: In keiner der drei Achsen ist ein Koerper gross, flach "
            "und unten — die Szene traegt kein erkennbares Gelaende. Ohne Gelaende sagt "
            "die Form nichts ueber oben: Ein Turm ist in der Hochachse die groesste "
            "Ausdehnung, ein Flachbau die kleinste, und beide sehen der Messung gleich "
            "aus."
            + (f" {unklar} Koerper blieben 'nicht entscheidbar' (gross und flach, aber "
               f"zu hoch)." if unklar else ""))
        return ergebnis

    if s_zweite > 0.0:
        ergebnis["vorsprung"] = s_beste / s_zweite
        if ergebnis["vorsprung"] < VORSPRUNG_MIN:
            ergebnis["grund"] = MEHRDEUTIG
            ergebnis["satz"] = (
                f"NICHT ENTSCHEIDBAR: Zwei Achsen tragen einen Gelaendebefund — {beste} "
                f"mit Staerke {s_beste:.2f}, {zweite} mit {s_zweite:.2f}, Vorsprung "
                f"{ergebnis['vorsprung']:.1f} unter den verlangten "
                f"{VORSPRUNG_MIN:.1f}. Eine grosse duenne Platte sieht gleich aus, ob "
                f"sie liegt oder steht; hier gibt es zwei, und welche liegt, entscheidet "
                f"die Form nicht.")
            return ergebnis
        ergebnis["sicherheit"] = "knapp"
    else:
        ergebnis["sicherheit"] = "eindeutig"

    if beste not in VERTRAGSACHSEN:
        ergebnis["grund"] = AUSSERHALB_DES_VERTRAGS
        ergebnis["sicherheit"] = None
        ergebnis["satz"] = (
            f"NICHT ENTSCHEIDBAR: Gemessen antwortet die Achse {beste} (Staerke "
            f"{s_beste:.2f}) — und die kennt der Vertrag nicht, er laesst nur "
            f"{' und '.join(VERTRAGSACHSEN)} zu. Entweder ist die Datei in einer dritten "
            f"Konvention geschrieben, oder eine grosse duenne Platte steht senkrecht und "
            f"sieht der Messung wie Gelaende aus. Auf die zweitbeste Achse wird NICHT "
            f"ausgewichen.")
        return ergebnis

    ergebnis["achse"] = beste
    ergebnis["achse_index"] = ACHSEN.index(beste)
    ergebnis["grund"] = GEMESSEN
    ergebnis["entschieden_durch_familie"] = (
        je_achse[beste]["n_gelaende_einzeln"] == 0 < je_achse[beste]["n_gelaende"])
    m = je_achse[beste]
    ergebnis["satz"] = (
        f"Gemessen ist {beste} oben: {m['n_gelaende']} Koerper "
        f"{'ist' if m['n_gelaende'] == 1 else 'sind'} in dieser Achse gross und flach "
        f"und {'liegt' if m['n_gelaende'] == 1 else 'liegen'} unten "
        f"(zusammen {m['grundrissanteil']:.0%} der Grundflaeche, "
        f"Flachheit {m['flachheit']:.3f}, Oberkante bei {m['tieflage']:.0%} der "
        f"Szenenhoehe). "
        + ("In keiner anderen Achse gibt es einen solchen Koerper."
           if ergebnis["vorsprung"] is None else
           f"Die zweitbeste Achse {zweite} kommt auf {s_zweite:.2f}, Vorsprung "
           f"{ergebnis['vorsprung']:.1f}.")
        + (" Entschieden hat die Familienpruefung: einzeln galt kein Koerper als "
           "Gelaende, die Huellbox ueber die Namensfamilie schon."
           if ergebnis["entschieden_durch_familie"] else ""))
    return ergebnis


def hochachse_aus_geometrie(pfad, *, als_familie: bool = True) -> dict:
    """Dieselbe Messung, aber aus einer ``.glb``/``.gltf`` heraus.

    Liest nur den JSON-Kopf (:func:`aiimaging.glbbox.lies_gltf_json`) — keine Dreiecke,
    kein Blender, Millisekunden.

    **Knoten ohne ``min``/``max`` beenden die Messung mit ``None``**, sie werden nicht
    übergangen: Genau der fehlende Körper könnte das Gelände sein, und eine Achse, die
    an einem Ausschnitt gemessen wurde, sähe der fertigen Antwort nicht an, dass sie es
    ist. Dieselbe Weigerung wie in :func:`aiimaging.glbbox.bauwerksbox`, nur als ``None``
    statt als Ausnahme — dieses Modul antwortet auf jede Frage, und «nicht messbar» ist
    hier eine Antwort.

    Raises:
        GlbError: Die Datei selbst ist nicht lesbar. Das ist keine Messfrage.
    """
    gelesen = knotenboxen(lies_gltf_json(pfad))
    if gelesen["ohne_grenzen"]:
        fehlend = gelesen["ohne_grenzen"]
        return {
            "achse": None, "achse_index": None, "sicherheit": None,
            "grund": OHNE_GRENZEN, "staerke": None, "vorsprung": None,
            "achsen": {}, "n_knoten": len(gelesen["knoten"]),
            "als_familie": bool(als_familie), "entschieden_durch_familie": False,
            "satz": (
                f"NICHT ENTSCHEIDBAR: {len(fehlend)} Mesh-Knoten tragen keinen "
                f"POSITION-Accessor mit min/max (zuerst: {fehlend[:3]}), obwohl glTF 2.0 "
                f"beides verlangt. Auf dem Rest gemessen koennte gerade das Gelaende "
                f"fehlen — und der Antwort waere nicht anzusehen, dass sie auf einem "
                f"Ausschnitt beruht."),
        }
    return hochachse_aus_knoten(gelesen["knoten"], als_familie=als_familie)


def gegenprobe(angabe, befund: dict) -> dict:
    """Hält eine **Angabe** gegen die **Messung**.

    Args:
        angabe: Was die Datei oder der Auftrag behauptet. Wird mit
            :func:`aiimaging.contracts.normalize_up_axis` gelesen — derselben Funktion,
            die im Vertrag steht, damit hier keine zweite Deutung entsteht.
        befund: Das Ergebnis von :func:`hochachse_aus_knoten` oder
            :func:`hochachse_aus_geometrie`.

    Returns:
        dict mit ``angegeben``, ``gemessen``, ``stimmt`` und ``satz``.

        **``stimmt`` kennt drei Werte, und der dritte ist der wichtigste:**

        * ``True`` — Angabe und Messung sagen dasselbe.
        * ``False`` — sie widersprechen sich.
        * ``None`` — **NICHT GEMESSEN.** Kein Urteil über die Angabe, weder gut noch
          schlecht. Wer dieses ``None`` als ``False`` liest, meldet einen Fehler, den
          niemand gefunden hat; wer es als ``True`` liest, meldet eine Prüfung, die
          nie stattfand. Beides ist schlimmer als das ``None``.

    *Und bei ``False`` steht kein Urteil über die Angabe.* Die Messung kann irren — eine
    stehende Platte sieht ihr wie Gelände aus (Modulkopf). Gemeldet wird darum ein
    **Widerspruch**, der von Hand aufzulösen ist, kein Befund gegen den Aufrufer.

    Raises:
        ContractError: Die Angabe ist gar keine Achsenangabe. Das ist kein
            Messergebnis, sondern ein Vertragsbruch, und er gehört laut gemeldet —
            genau wie in :func:`aiimaging.contracts.normalize_up_axis`.
    """
    angegeben = normalize_up_axis(angabe)
    gemessen = befund.get("achse")
    aus = {"angegeben": angegeben, "gemessen": gemessen, "stimmt": None,
           "satz": "", "befund": befund}

    if gemessen is None:
        # KEIN URTEIL. Nicht False, nicht True — und die Reihenfolge der Zweige ist hier
        # der ganze Punkt: Waere unten `stimmt = (angegeben == gemessen)` gerechnet,
        # ergaebe ein nicht gemessenes `None` still ein sauberes `False` und damit einen
        # gemeldeten Fehler, den niemand gefunden hat.
        aus["satz"] = (
            f"Die Angabe '{angegeben}' wurde NICHT GEPRUEFT: Die Geometrie gibt die "
            f"Hochachse nicht her. {befund.get('satz', '')}".strip())
        return aus

    aus["stimmt"] = (angegeben == gemessen)
    if aus["stimmt"]:
        aus["satz"] = (
            f"Angabe '{angegeben}' und Messung stimmen ueberein. {befund.get('satz', '')}"
        ).strip()
    else:
        aus["satz"] = (
            f"WIDERSPRUCH: Angegeben ist '{angegeben}', gemessen '{gemessen}'. "
            f"{befund.get('satz', '')} Welche der beiden Seiten irrt, sagt diese Probe "
            f"NICHT: Eine falsche Angabe dreht das Gebaeude, und eine grosse duenne "
            f"Platte, die senkrecht steht, fuehrt die Messung in die Irre. Beides ist "
            f"von Hand zu klaeren.").strip()
    return aus


def gegenprobe_datei(pfad, angabe, *, als_familie: bool = True) -> dict:
    """:func:`hochachse_aus_geometrie` und :func:`gegenprobe` in einem Griff."""
    return gegenprobe(angabe, hochachse_aus_geometrie(pfad, als_familie=als_familie))


__all__ = [
    "ACHSEN", "AUSSERHALB_DES_VERTRAGS", "GEMESSEN", "KEINE_AUSDEHNUNG", "KEINE_KNOTEN",
    "KEIN_GELAENDE", "MEHRDEUTIG", "OHNE_GRENZEN", "VERTRAGSACHSEN", "VORSPRUNG_MIN",
    "ContractError", "gegenprobe", "gegenprobe_datei", "hochachse_aus_geometrie",
    "hochachse_aus_knoten",
]
