"""Das erste Verbinden: eine kurze Zahl für einen Augenblick, ein langes Kennwort für immer.

Das Problem, das diese Datei löst
---------------------------------
Die HomeStation schützt ihre Oberfläche im Heimnetz mit einem Kennwort aus 32 zufälligen
Zeichen (Owner-Entscheid E25). Das ist für ein Kennwort richtig
und für das **erste Verbinden** unbrauchbar: Niemand tippt 32 Zeichen auf einem Tablet ab,
und wer es doch täte, tippte sie falsch.

    *Was nur über das Eintippen erreichbar ist, wird nicht benutzt.*

Der Ausweg ist alt und bewährt: **ein kurzes, schwaches Geheimnis für einen Augenblick
tauscht man gegen ein langes, starkes für immer.** Die HomeStation zeigt eine sechsstellige
Zahl. Das iPad tippt sie **einmal** ein und bekommt dafür das richtige Kennwort, das es
danach selbst aufbewahrt. Die Zahl ist danach tot.

Warum das sicher genug ist — und woran es hängt
-----------------------------------------------
Sechs Stellen sind eine Million Möglichkeiten. Das ist **nicht** viel; es trägt nur unter
drei Auflagen, und alle drei stehen im Code und nicht in einer Absichtserklärung:

1. **Sie lebt kurz.** Zehn Minuten, gerechnet auf einer Uhr, die nicht zurückspringen
   kann (siehe unten).
2. **Sie stirbt nach fünf Fehlversuchen.** Wer raten will, bekommt fünf Versuche, nicht
   eine Million. Danach muss jemand an der HomeStation eine neue zeigen lassen — also ein
   Mensch im selben Raum.
3. **Sie wird einmal verbraucht.** Nach dem ersten erfolgreichen Verbinden ist sie tot.
   Sonst verbände sich, wer über die Schulter gesehen hat, als Zweiter mit.

Die Uhr, und warum nicht die Wanduhr
------------------------------------
Die Frist läuft auf einer **stetigen Uhr** (``time.monotonic``), nicht auf der Wanduhr.
Eine Wanduhr lässt sich stellen — von Hand, von der Zeitumstellung, von einem Zeitserver.
Wer sie zurückstellt, verlängert eine Frist, die auf ihr gerechnet wird.

    *Eine Sperre, die eine falsch gehende Uhr aufbricht, ist keine Sperre. Sie ist eine
    Verzögerung.*

Dieselbe Überlegung wie bei der Laufsperre in :mod:`aiimaging.arbeitsgang` (21.09.2026),
nur strenger: Dort werden zwei Quellen verglichen und die jüngere gewinnt; hier gibt es
gar keine zweite Quelle, an der sich drehen liesse.

Zwei Sätze, nicht einer
-----------------------
Ein abgelehnter Versuch liefert **zwei** Begründungen:

* ``grund`` — genau, für den Menschen **an der HomeStation**: abgelaufen, falsch,
  aufgebraucht, schon verbraucht. Er steht dort vor dem Gerät und muss wissen, was zu tun
  ist.
* ``satz_fuer_das_geraet`` — absichtlich **unbestimmt**, für das iPad: «Das hat nicht
  geklappt.» Wer eine Zahl rät, soll nicht erfahren, ob er an der Zahl oder an der Frist
  gescheitert ist; das halbierte sonst seine Arbeit.

    *Wer beim Raten erfährt, warum er daneben lag, rät beim nächsten Mal besser.*

Was hier NICHT drin ist
-----------------------
* **Kein Kennwort.** Dieses Modul erzeugt, prüft und verbraucht die kurze Zahl. Was nach
  dem Gelingen übergeben wird, entscheidet der Aufrufer.

  *Und es weiss auch nicht, WER der Aufrufer ist.* Regel 4 gilt in beide Richtungen: Der
  Kern nennt die Fläche nirgends, nicht einmal in einem Satz zur Erklärung. Ein Wächter
  hält das fest, und er hat diese Datei beim ersten Anlauf abgewiesen — zu Recht.
* **Keine Netzverbindung, keine Oberfläche, kein Zustand auf der Platte.** Regel 4: Alles
  hier ist aus Python heraus benutzbar, ohne dass irgendetwas läuft.
* **Kein Finden im Netz.** Wie das iPad die Adresse der HomeStation erfährt, ist eine
  andere Frage und steht in ``docs/PLAN.md`` als eigener Posten.
"""
from __future__ import annotations

import hmac
import secrets
import time
from dataclasses import dataclass, field

__all__ = [
    "FRIST_S", "PIN_STELLEN", "VERSUCHE",
    "GRUND_ABGELAUFEN", "GRUND_AUFGEBRAUCHT", "GRUND_FALSCH", "GRUND_VERBRAUCHT",
    "SATZ_FUER_DAS_GERAET",
    "STAND_ABGELAUFEN", "STAND_AUFGEBRAUCHT", "STAND_OFFEN", "STAND_VERBRAUCHT",
    "Kopplung", "KopplungError", "eroeffne", "pruefe", "schliesse", "stand",
]


class KopplungError(ValueError):
    """Die Kopplung selbst ist nicht brauchbar — nicht der Versuch daran.

    Derselbe Unterschied wie überall in diesem Projekt: Ein **falsch geratener** Versuch
    ist ein Befund und kommt als Antwort zurück. Eine Kopplung mit null Versuchen oder
    negativer Frist ist ein Fehler des Aufrufers und wirft.
    """


#: Wie lange eine Zahl gilt. Zehn Minuten reichen, um vom Rechner zum Tablet zu gehen und
#: sechs Ziffern zu tippen — und sie sind kurz genug, dass ein Bildschirmfoto davon
#: morgen nichts mehr wert ist.
FRIST_S = 600.0

#: Sechs Stellen. Fünf wären bequemer und eine Zehntelmillion schwächer; acht wären
#: stärker und würden falsch abgetippt. Sechs ist die Länge, die Menschen aus dem
#: Kurzzeitgedächtnis fehlerfrei übertragen.
PIN_STELLEN = 6

#: Wie oft geraten werden darf. Fünf, und danach ist die Zahl tot — nicht «gesperrt für
#: eine Minute». Eine Sperre auf Zeit lädt zum Warten ein; eine tote Zahl verlangt einen
#: Menschen an der HomeStation.
VERSUCHE = 5

STAND_OFFEN = "offen"
STAND_ABGELAUFEN = "abgelaufen"
STAND_AUFGEBRAUCHT = "aufgebraucht"
STAND_VERBRAUCHT = "verbraucht"

GRUND_FALSCH = "Die Zahl stimmt nicht."
GRUND_ABGELAUFEN = "Die Zahl ist abgelaufen. An der HomeStation eine neue zeigen lassen."
GRUND_AUFGEBRAUCHT = ("Zu oft daneben. Die Zahl ist tot — an der HomeStation eine neue "
                      "zeigen lassen.")
GRUND_VERBRAUCHT = ("Diese Zahl hat schon ein Gerät verbunden. Für ein zweites braucht es "
                    "eine neue.")

#: Was das Gerät zu hören bekommt — **immer dasselbe, egal woran es lag.**
SATZ_FUER_DAS_GERAET = "Das hat nicht geklappt. An der HomeStation eine neue Zahl holen."


@dataclass
class Kopplung:
    """Eine offene Kopplung: die Zahl, ihre Frist und was von ihr übrig ist.

    Der Zustand liegt **im Arbeitsspeicher und nirgends sonst**. Eine Kopplung, die einen
    Neustart überlebte, wäre eine Zahl, die jemand vor drei Wochen abgelesen hat — und der
    ganze Sinn der kurzen Frist wäre dahin.

    Attributes:
        pin: Die Zahl als Zeichenkette mit führenden Nullen. Sie gehört an den Bildschirm
            der HomeStation und in **kein Protokoll** (siehe `tests/test_kopplung.py`).
        faellig: Der Zeitpunkt auf der stetigen Uhr, ab dem sie nicht mehr gilt.
        versuche_uebrig: Wie oft noch geraten werden darf.
        verbraucht: Ob schon ein Gerät damit verbunden hat.
    """

    pin: str
    faellig: float
    versuche_uebrig: int
    verbraucht: bool = False
    #: Nur zur Anzeige — die Wanduhrzeit, zu der sie erzeugt wurde. Es wird **nichts**
    #: darauf gerechnet; siehe den Modulkopf.
    gezeigt_um: str = field(default="")


def _uhr(jetzt) -> float:
    """Die stetige Uhr, oder der Wert, den ein Test vorgibt."""
    return time.monotonic() if jetzt is None else float(jetzt)


def eroeffne(*, jetzt=None, frist_s: float = FRIST_S, versuche: int = VERSUCHE,
             _pin: str | None = None) -> Kopplung:
    """Eine neue Zahl erzeugen und die Frist starten.

    Args:
        jetzt: Der Stand der stetigen Uhr. ``None`` heisst «jetzt». Für Tests.
        frist_s: Wie lange die Zahl gilt.
        versuche: Wie oft geraten werden darf.
        _pin: Eine vorgegebene Zahl. **Nur für Tests** — Unterstrich, weil es eine Naht
            ist und keine Einstellung. Eine selbstgewählte Zahl im Betrieb wäre eine
            ausgedachte, und ausgedachte Zahlen sind ratbar.

    Raises:
        KopplungError: Frist oder Versuche sind nicht positiv. Eine Kopplung mit null
            Versuchen ist keine Kopplung, sondern eine Attrappe — und sie sähe im
            Betrieb genauso aus wie eine echte.
    """
    if frist_s <= 0:
        raise KopplungError(
            f"Eine Frist von {frist_s} Sekunden ist keine Frist. Wer keine will, erzeugt "
            f"keine Kopplung.")
    if versuche <= 0:
        raise KopplungError(
            f"{versuche} Versuche heisst: Diese Zahl lässt sich nie eingeben. Das sieht "
            f"im Betrieb aus wie eine falsch abgetippte Zahl und ist keine.")

    pin = _pin if _pin is not None else _wuerfle()
    return Kopplung(
        pin=pin,
        faellig=_uhr(jetzt) + float(frist_s),
        versuche_uebrig=int(versuche),
        gezeigt_um=time.strftime("%Y-%m-%d %H:%M:%S"),
    )


def _wuerfle() -> str:
    """Eine Zahl, die **niemand sich ausgedacht hat** — gleichverteilt über alle Stellen.

    ``secrets`` und nicht ``random``, aus demselben Grund wie beim Kennwort: Die Folge von
    ``random`` lässt sich aus wenigen Werten fortrechnen. *Ein Zufall, der sich
    fortrechnen lässt, ist keiner.*

    Und **nichts wird ausgeschlossen** — kein ``000000``, keine Folge, kein Geburtsjahr.
    Wer «schwache» Zahlen aussortiert, verkleinert den Vorrat und sagt dem Ratenden damit,
    wonach er nicht suchen muss.
    """
    return str(secrets.randbelow(10 ** PIN_STELLEN)).zfill(PIN_STELLEN)


def stand(kopplung: Kopplung, *, jetzt=None) -> str:
    """Woran man ist, ohne etwas zu verbrauchen.

    Die Reihenfolge ist ein Entscheid: **verbraucht** vor **abgelaufen** vor
    **aufgebraucht**. Eine Zahl, die ein Gerät verbunden hat, ist verbraucht — auch wenn
    inzwischen die Frist abgelaufen ist. Der erste Grund ist der, der zuerst eintrat, und
    der Mensch an der HomeStation will wissen, was passiert ist, nicht was zuletzt galt.
    """
    if kopplung.verbraucht:
        return STAND_VERBRAUCHT
    if _uhr(jetzt) >= kopplung.faellig:
        return STAND_ABGELAUFEN
    if kopplung.versuche_uebrig <= 0:
        return STAND_AUFGEBRAUCHT
    return STAND_OFFEN


def pruefe(kopplung: Kopplung, eingabe, *, jetzt=None) -> dict:
    """Einen Versuch prüfen — und ihn zählen.

    Returns:
        ``{angenommen, stand, grund, satz_fuer_das_geraet, versuche_uebrig}``.
        ``grund`` ist leer, wenn es geklappt hat.

    **Der Vergleich läuft über** :func:`hmac.compare_digest` **und nicht über** ``==``.
    Ein gewöhnlicher Vergleich bricht bei der ersten abweichenden Stelle ab und braucht
    darum für «1xxxxx» messbar länger als für «9xxxxx», wenn die Zahl mit 1 beginnt. Über
    ein Heimnetz ist dieser Unterschied klein — *aber eine Vorsichtsmassnahme, die nur
    dort greift, wo man sie für nötig hält, greift irgendwann nicht mehr.*

    **Ein Versuch wird auch dann gezählt, wenn die Zahl stimmt und die Frist abgelaufen
    ist.** Sonst liesse sich über eine tote Zahl beliebig oft raten, ohne dass der Zähler
    sich bewegte — und der Zähler ist die einzige Schranke, die nicht von der Uhr abhängt.
    """
    lage = stand(kopplung, jetzt=jetzt)
    if lage != STAND_OFFEN:
        gruende = {STAND_VERBRAUCHT: GRUND_VERBRAUCHT,
                   STAND_ABGELAUFEN: GRUND_ABGELAUFEN,
                   STAND_AUFGEBRAUCHT: GRUND_AUFGEBRAUCHT}
        return _antwort(False, lage, gruende[lage], kopplung.versuche_uebrig)

    kopplung.versuche_uebrig -= 1
    gegeben = eingabe if isinstance(eingabe, str) else ""
    # Vor dem Vergleich wird Leerraum weggenommen — ein Tablet haengt beim Einfuegen gern
    # ein Leerzeichen an, und daran soll niemand scheitern. Mehr NICHT: Wer «1 2 3 4 5 6»
    # zusammenzoege, machte aus zwei verschiedenen Eingaben dieselbe.
    stimmt = hmac.compare_digest(gegeben.strip(), kopplung.pin)

    if not stimmt:
        rest = kopplung.versuche_uebrig
        return _antwort(False, stand(kopplung, jetzt=jetzt),
                        GRUND_FALSCH if rest > 0 else GRUND_AUFGEBRAUCHT, rest)

    kopplung.verbraucht = True
    return _antwort(True, STAND_VERBRAUCHT, "", kopplung.versuche_uebrig)


def schliesse(kopplung: Kopplung) -> None:
    """Die Zahl von Hand für ungültig erklären.

    Gebraucht, wenn jemand sie versehentlich gezeigt hat und nicht zehn Minuten warten
    will. *Eine Sperre, die man nur durch Abwarten wieder los wird, wartet niemand ab.*
    """
    kopplung.verbraucht = True


def _antwort(angenommen: bool, lage: str, grund: str, rest: int) -> dict:
    return {
        "angenommen": angenommen,
        "stand": lage,
        # FUER DEN MENSCHEN AN DER HOMESTATION: genau.
        "grund": grund,
        # FUER DAS GERAET: immer derselbe Satz, damit das Raten nicht billiger wird.
        "satz_fuer_das_geraet": "" if angenommen else SATZ_FUER_DAS_GERAET,
        "versuche_uebrig": max(0, rest),
    }
