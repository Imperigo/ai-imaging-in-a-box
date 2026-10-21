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
Je Geräteart (heute nur ``ipad``) **drei Angaben, alle ohne Geheimnis:**

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
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

__all__ = [
    "ARTEN", "DATEINAME", "SATZ_DIREKT_BEENDET", "SCHREIBABSTAND_S", "WEGE",
    "antwort", "direkt_vom_ipad", "gemerkt", "lies", "schreibe", "vermerke_anfrage", "vermerke_kopplung",
    "zum_schreiben",
]

#: Die Gerätearten, die im Buch stehen dürfen. Der Mac steht **nicht** darin: Er fragt das
#: Buch selbst ab, und seine eigene Leitung zeigt er schon in der ersten Startzeile.
ARTEN = ("ipad",)

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


def direkt_vom_ipad(geraet, weg) -> bool:
    """Ob eine Anfrage von einem iPad **direkt** kommt — ``X-Geraet: ipad`` ohne
    ``X-Geraet-Weg: mac`` (Entscheid 118a). Gross- und Kleinschreibung und Leerraum am Rand
    zählen nicht; ein fehlender Gerätekopf heisst «kein iPad», nicht «direkt».
    """
    if (geraet or "").strip().lower() != "ipad":
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
    for art in ARTEN:
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
    if art not in ARTEN:
        raise ValueError(f"Die Geräteart {art!r} steht nicht im Buch — nur {', '.join(ARTEN)}.")


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
                        if art in ARTEN}}


def antwort(buch: dict, *, jetzt=None) -> dict:
    """Die Antwort an den Mac: je Art ``gekoppelt``, ``gekoppelt_vor_s``,
    ``zuletzt_gesehen_s`` (Sekunden seit der letzten Meldung) und ``weg``.

    ``gekoppelt`` heisst: Eine Zahl wurde angenommen **oder** eine angemeldete Anfrage kam.
    Wie lange «zuletzt gesehen» noch als «da» gilt, entscheidet **der Mac** (Kern,
    ``Ipadzeile``) — der Heim-PC meldet nur, was er weiss. Eine Zeit in der Zukunft (die Uhr
    wurde zurückgestellt) zählt als «eben».
    """
    t = _jetzt(jetzt)
    aus = {}
    for art in ARTEN:
        e = (buch.get("geraete") or {}).get(art) or {}
        gek, zul = e.get("gekoppelt_um"), e.get("zuletzt_um")
        aus[art] = {
            "gekoppelt": gek is not None or zul is not None,
            "gekoppelt_vor_s": None if gek is None else int(max(0.0, t - gek)),
            "zuletzt_gesehen_s": None if zul is None else int(max(0.0, t - zul)),
            "weg": e.get("weg"),
        }
    return aus
