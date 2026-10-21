"""Das Gerätebuch: ob am Heim-PC ein iPad gekoppelt ist, und wann es sich zuletzt meldete.

Der Anlass (Owner-Befund vom 20.10.2026, Visbox 0.2.11)
-------------------------------------------------------
Das iPad zeigte «Gekoppelt · über Tailscale · antwortet», der Heim-PC schrieb «Ein Gerät hat
sich verbunden». Der Mac aber zeigte die Zeile «iPad» weiter als «wartet» und bot immer neue
Zahlen an — er wusste es nicht. Gekoppelt hatte das iPad **direkt mit dem Heim-PC**; der Mac
kannte nur, was über ihn selbst lief (die Vermittlung), und der Heim-PC hielt die Kopplung
nur als verbrauchte Zahl im Arbeitsspeicher.

    *Wer als Einziger dabei war, muss es aufschreiben — sonst weiss es nachher keiner.*

Darum führt der Heim-PC dieses kleine Buch, und der Mac fragt es ab.

Was darin steht — und was nie
-----------------------------
Je Geräteart (heute nur ``ipad``, dazu der Probename ``ipad-probe``) **drei Angaben, alle ohne Geheimnis:**

* ``gekoppelt_um`` — wann zuletzt eine Zahl für dieses Gerät angenommen wurde (Unix-Zeit, s),
* ``zuletzt_um`` — wann zuletzt eine angemeldete Anfrage von ihm kam,
* ``weg`` — wie sie kam: ``direkt`` (über Tailscale oder im Heimnetz) oder ``mac`` (über die
  Vermittlung des Mac).

**Nie** darin: ein Kennwort, eine Zahl, eine Adresse, ein Gerätename. Die Geräteart sagt das
Gerät selbst in einem Kopf ohne Geheimnis (``X-Geraet``); ein Name bliebe hier liegen
und verriete, wessen Tablet es ist (Regel 3).

Die Uhr, und warum hier die Wanduhr
-----------------------------------
Anders als bei :mod:`aiimaging.kopplung` wird hier **nichts entschieden, was schützt**: Das
Buch sagt nur, was der Mac anzeigt. Es soll einen Neustart überleben, und das kann nur die
Wanduhr — die stetige Uhr beginnt bei jedem Start neu. Stellt jemand die Uhr, irrt höchstens
die Anzeige «zuletzt vor …», nie eine Tür.

Wie oft geschrieben wird
------------------------
Das iPad fragt alle zehn Sekunden. Jede Anfrage auf die Platte zu schreiben, hiesse
8640 Schreibvorgänge am Tag für eine Anzeige, die auf die Minute genügt. Geschrieben wird
darum **bei jeder Kopplung, bei jedem Wechsel des Wegs und sonst höchstens einmal je
:data:`SCHREIBABSTAND_S`**; im Arbeitsspeicher steht immer der neueste Stand.

Der direkte Weg endet (Owner-Entscheid 118a, 21.10.2026)
---------------------------------------------------------
Seit Entscheid 118 arbeitet das iPad **über den Mac**: Die Mappe liegt dort, und ein iPad, das
direkt mit dem Heim-PC spricht, sähe einen zweiten Stand derselben Arbeit. In 0.3.16 ging der
direkte Weg noch, mit Hinweis (Übergang). Seither weist der Heim-PC ein iPad, das direkt
spricht, **mit einem Satz ab** (:func:`direkt_vom_ipad`, :data:`SATZ_DIREKT_BEENDET`, Antwort
410). Woran es erkennbar ist: ``X-Geraet: ipad`` ohne ``X-Geraet-Weg: mac`` — den Wegkopf setzt
die Vermittlung des Mac an jede Anfrage, die sie weiterreicht. Wer keinen Gerätekopf schickt
(Mac-App mit ``mac``, Visbox-Seite, KosmoOrbit, die Werkzeuge der HomeStation), ist nicht
gemeint.

Die Probe schreibt nicht ins Blatt des echten iPad (Befund 308 B1, 21.10.2026)
------------------------------------------------------------------------------
Bis 0.3.18 führte das Buch **je Geräteart** einen Eintrag. Als die HomeStation den Weg über
den Mac prüfte (``X-Geraet: ipad``, ``X-Geraet-Weg: mac``), überschrieb ihre eine Anfrage
den Eintrag des echten iPad: ``weg direkt → mac``, ``zuletzt_um`` neu. Der Mac zeigte danach
«über den Mac, gerade gesehen», obwohl kein iPad da war.

Eine Kennung je Gerät gibt es nicht und soll es nicht geben: Das iPad schickt keine, und
über den Mac käme ohnehin nur, was der Mac setzt — die Vermittlung wirft die Köpfe des iPad
weg und hängt ``X-Geraet: ipad`` selbst an (``Vermittlungsanfrage.koepfe(mit:)``). Eine
dauerhafte Kennung im Buch wäre zudem ein Merkmal, das ein Tablet wiedererkennbar macht
(Regel 3). Darum gibt es **einen Probenamen**: ``X-Geraet: ipad-probe``
(:data:`PROBEARTEN`). Er wird an der Tür **wie ein iPad** behandelt (direkt: 410 mit Satz;
über den Mac: durch), steht aber in einem **eigenen Eintrag**, und die Antwort an den Mac
nennt ihn nur, wenn es ihn gibt — der Mac liest allein ``ipad``. Ein echtes iPad kann den
Probenamen nicht tragen: Über den Mac ist er weg, direkt endet er bei 410.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

__all__ = [
    "ARTEN", "BUCHARTEN", "DATEINAME", "PROBEARTEN", "SATZ_DIREKT_BEENDET", "SCHREIBABSTAND_S", "WEGE",
    "antwort", "bereinige_fehleintrag", "direkt_vom_ipad", "steht_fuer", "gemerkt", "lies", "schreibe", "vermerke_anfrage", "vermerke_kopplung",
    "zum_schreiben",
]

#: Die Gerätearten, die im Buch stehen dürfen. Der Mac steht **nicht** darin: Er fragt das
#: Buch selbst ab, und seine eigene Leitung zeigt er schon in der ersten Startzeile.
ARTEN = ("ipad",)

#: Probenamen (Befund 308 B1): je Name die Art, **für die er steht**. Eine Probe der
#: HomeStation sagt ``X-Geraet: ipad-probe`` und wird an der Tür wie ein iPad behandelt, aber
#: in einem eigenen Eintrag geführt — das Blatt des echten iPad bleibt, wie es war.
PROBEARTEN = {"ipad-probe": "ipad"}

#: Alles, was im Buch einen Eintrag haben darf: die echten Arten und die Probenamen.
BUCHARTEN = ARTEN + tuple(PROBEARTEN)

#: Wie eine Anfrage kam.
WEGE = ("direkt", "mac")

#: Der Dateiname neben der Kennwortdatei (im Dienstordner, ausserhalb des Repos).
DATEINAME = "geraete.json"

#: Höchstens so oft wird eine blosse Meldung («es fragt wieder») auf die Platte geschrieben.
SCHREIBABSTAND_S = 60.0

#: Der Satz für ein iPad, das direkt mit dem Heim-PC spricht (Entscheid 118a). Er sagt, was
#: zu tun ist — ohne Rechnernamen, ohne Adresse.
SATZ_DIREKT_BEENDET = ("Das iPad verbindet sich jetzt über den Mac — am Mac «iPad koppeln» "
                       "öffnen und das iPad mit dem Mac koppeln. Direkt nimmt der Heim-PC "
                       "das iPad nicht mehr an.")


def steht_fuer(art) -> str | None:
    """Die Art, für die ``art`` an der Tür steht: ``ipad`` für ``ipad`` und ``ipad-probe``,
    sonst ``None``. Gross- und Kleinschreibung und Leerraum am Rand zählen nicht."""
    a = (art or "").strip().lower()
    return a if a in ARTEN else PROBEARTEN.get(a)


def direkt_vom_ipad(geraet, weg) -> bool:
    """Ob eine Anfrage von einem iPad **direkt** kommt — ``X-Geraet: ipad`` (oder der
    Probename ``ipad-probe``) ohne ``X-Geraet-Weg: mac`` (Entscheid 118a). Gross- und
    Kleinschreibung und Leerraum am Rand zählen nicht; ein fehlender Gerätekopf heisst «kein
    iPad», nicht «direkt».
    """
    if steht_fuer(geraet) != "ipad":
        return False
    return (weg or "").strip().lower() != "mac"


def _jetzt(jetzt) -> float:
    return time.time() if jetzt is None else float(jetzt)


def _leer() -> dict:
    return {"geraete": {}}


def lies(datei) -> dict:
    """Das Buch aus ``datei`` — oder ein leeres, wenn es keine gibt oder sie nicht lesbar ist.

    **Ein kaputtes Buch hält nichts auf:** Es zeigt nur an, was der Mac sieht. Leer heisst
    dann «noch nicht gesehen» — wahr bis zur nächsten Anfrage des iPad, die es neu schreibt.
    Was nicht in der erwarteten Form ist (eine fremde Art, ein Weg, den es nicht gibt, eine
    Zeit, die keine Zahl ist), wird weggelassen, nicht geraten.
    """
    if datei is None:
        return _leer()
    try:
        roh = json.loads(Path(datei).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _leer()
    buch = _leer()
    geraete = roh.get("geraete") if isinstance(roh, dict) else None
    if not isinstance(geraete, dict):
        return buch
    for art in BUCHARTEN:
        eintrag = geraete.get(art)
        if not isinstance(eintrag, dict):
            continue
        sauber = {}
        for feld in ("gekoppelt_um", "zuletzt_um"):
            wert = eintrag.get(feld)
            if isinstance(wert, (int, float)) and not isinstance(wert, bool) and wert > 0:
                sauber[feld] = float(wert)
        if eintrag.get("weg") in WEGE:
            sauber["weg"] = eintrag["weg"]
        if sauber:
            buch["geraete"][art] = sauber
    return buch


def schreibe(datei, buch: dict) -> None:
    """Das Buch nach ``datei`` — **nur für den eigenen Benutzer lesbar** (0600), wie die
    Kennwortdatei daneben, und **ganz oder gar nicht** (erst eine Nebendatei, dann umbenannt):
    Ein Neustart mitten im Schreiben soll kein halbes Buch hinterlassen."""
    pfad = Path(datei)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    neben = pfad.with_name(pfad.name + ".neu")
    fd = os.open(neben, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(buch, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    os.chmod(neben, 0o600)
    os.replace(neben, pfad)


def _pruefe_art(art: str) -> None:
    if art not in BUCHARTEN:
        raise ValueError(f"Die Geräteart {art!r} steht nicht im Buch — nur "
                         f"{', '.join(BUCHARTEN)}.")


def vermerke_kopplung(buch: dict, art: str, *, weg: str = "direkt", jetzt=None) -> bool:
    """Eine angenommene Zahl für ``art`` vermerken. Gibt ``True`` zurück: **gleich schreiben**
    — eine Kopplung ist selten und soll einen Neustart sicher überleben.

    Die Kopplung zählt zugleich als Meldung: Wer eben gekoppelt hat, war eben da.
    """
    _pruefe_art(art)
    if weg not in WEGE:
        raise ValueError(f"Der Weg {weg!r} ist keiner — nur {', '.join(WEGE)}.")
    t = _jetzt(jetzt)
    eintrag = buch.setdefault("geraete", {}).setdefault(art, {})
    eintrag["gekoppelt_um"] = t
    eintrag["zuletzt_um"] = t
    eintrag["weg"] = weg
    return True


def vermerke_anfrage(buch: dict, art: str, *, weg: str, jetzt=None,
                     abstand_s: float = SCHREIBABSTAND_S) -> bool:
    """Eine angemeldete Anfrage von ``art`` vermerken. Gibt zurück, ob **jetzt geschrieben**
    werden soll: beim ersten Mal, bei einem anderen Weg, oder wenn der letzte geschriebene
    Stand älter als ``abstand_s`` ist.

    **Eine Anfrage mit Kennwort heisst: gekoppelt.** Wer das Kennwort hat, hat es über eine
    Kopplung bekommen — auch wenn sie vor diesem Buch lag (ein iPad, das vor 0.2.12 gekoppelt
    wurde). Die Zeit der Kopplung bleibt dann unbekannt.
    """
    _pruefe_art(art)
    if weg not in WEGE:
        raise ValueError(f"Der Weg {weg!r} ist keiner — nur {', '.join(WEGE)}.")
    t = _jetzt(jetzt)
    eintrag = buch.setdefault("geraete", {}).setdefault(art, {})
    vorher = eintrag.get("zuletzt_um")
    vorher_weg = eintrag.get("weg")
    eintrag["zuletzt_um"] = t
    eintrag["weg"] = weg
    geschrieben = buch.setdefault("_geschrieben_um", {}).get(art)
    if vorher is None or vorher_weg != weg:
        return True
    return geschrieben is None or t - geschrieben >= abstand_s


def gemerkt(buch: dict, art: str, *, jetzt=None) -> None:
    """Vermerkt, dass der Stand von ``art`` eben geschrieben wurde (für den Abstand)."""
    buch.setdefault("_geschrieben_um", {})[art] = _jetzt(jetzt)


def zum_schreiben(buch: dict) -> dict:
    """Was auf die Platte geht — ohne die Buchhaltung des Schreibens."""
    return {"geraete": {art: dict(e) for art, e in (buch.get("geraete") or {}).items()
                        if art in BUCHARTEN}}


def antwort(buch: dict, *, jetzt=None) -> dict:
    """Die Antwort an den Mac: je Art ``gekoppelt``, ``gekoppelt_vor_s``,
    ``zuletzt_gesehen_s`` (Sekunden seit der letzten Meldung) und ``weg``.

    ``gekoppelt`` heisst: Eine Zahl wurde angenommen **oder** eine angemeldete Anfrage kam.
    Wie lange «zuletzt gesehen» noch als «da» gilt, entscheidet **der Mac** (Kern,
    ``Ipadzeile``) — der Heim-PC meldet nur, was er weiss. Eine Zeit in der Zukunft (die Uhr
    wurde zurückgestellt) zählt als «eben».

    Ein Probename (:data:`PROBEARTEN`) steht **nur darin, wenn es ihn gibt** — die HomeStation
    sieht so, was ihre Probe vermerkt hat; der Mac liest allein ``ipad``.
    """
    t = _jetzt(jetzt)
    aus = {}
    geraete = buch.get("geraete") or {}
    for art in ARTEN + tuple(a for a in PROBEARTEN if a in geraete):
        e = geraete.get(art) or {}
        gek, zul = e.get("gekoppelt_um"), e.get("zuletzt_um")
        aus[art] = {
            "gekoppelt": gek is not None or zul is not None,
            "gekoppelt_vor_s": None if gek is None else int(max(0.0, t - gek)),
            "zuletzt_gesehen_s": None if zul is None else int(max(0.0, t - zul)),
            "weg": e.get("weg"),
        }
    return aus


def bereinige_fehleintrag(buch: dict, art: str, *, zuletzt_um: float, weg: str = "mac") -> dict:
    """Einen **nachgewiesenen** Fehleintrag aus einer Probe zurücknehmen (Befund 311 B1).

    **Warum nicht beim Laden von selbst:** Die drei Felder (``gekoppelt_um``, ``zuletzt_um``,
    ``weg``) sagen nicht, wer die Anfrage schickte. Ein Eintrag ``weg: mac``, den die Probe aus
    308 schrieb, sieht genau so aus wie der eines echten iPad, das über den Mac kam — eine
    Regel beim Laden würde früher oder später den echten Stand löschen. Der Nachweis kommt
    darum von aussen: Wer bereinigt, nennt ``zuletzt_um`` **auf die Sekunde genau** so, wie es
    im Buch steht (gelesen aus dem Ergebnis, das den Fehleintrag gemeldet hat), und den Weg.
    Nur wenn beides passt, werden ``zuletzt_um`` und ``weg`` gestrichen; ``gekoppelt_um``
    bleibt (gekoppelt war das iPad wirklich). Der Mac zeigt dann «gekoppelt, noch nicht
    gesehen», bis das echte iPad wieder fragt — wahr, statt «über den Mac, gerade gesehen».

    Returns:
        ``{bereinigt, grund, vorher, nachher}`` — ``bereinigt`` ``False`` mit Grund, wenn der
        Eintrag fehlt oder nicht genau passt (dann bleibt alles, wie es ist).
    """
    _pruefe_art(art)
    eintrag = (buch.get("geraete") or {}).get(art)
    vorher = dict(eintrag) if isinstance(eintrag, dict) else None
    if not vorher:
        return {"bereinigt": False, "grund": f"Kein Eintrag {art!r} im Buch.", "vorher": None,
                "nachher": None}
    if vorher.get("weg") != weg or vorher.get("zuletzt_um") is None or \
            int(vorher["zuletzt_um"]) != int(zuletzt_um):
        return {"bereinigt": False, "vorher": vorher, "nachher": vorher, "grund": (
            f"Der Eintrag {art!r} passt nicht zum genannten Fehleintrag (weg {vorher.get('weg')!r}, "
            f"zuletzt_um {vorher.get('zuletzt_um')!r} gegen {weg!r}, {int(zuletzt_um)}) — "
            f"vermutlich kam seither das echte Gerät. Nichts geändert.")}
    nachher = {k: v for k, v in vorher.items() if k not in ("zuletzt_um", "weg")}
    if nachher:
        buch["geraete"][art] = nachher
    else:
        del buch["geraete"][art]
    return {"bereinigt": True, "grund": "", "vorher": vorher, "nachher": nachher or None}

