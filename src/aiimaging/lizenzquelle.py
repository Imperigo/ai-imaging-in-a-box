"""LIZENZQUELLE — eine Vokabel für die Herkunft einer Lizenzangabe, für alle Registries.

Warum dieses Modul existiert
----------------------------
Drei Registries führen dieselbe Angabe: :mod:`aiimaging.backbone` (Bildmodelle),
:mod:`aiimaging.einbetter` (Bild-Einbettungsmodelle) und
:mod:`aiimaging.tiefenschaetzer` (Tiefenschätzer). Jede trägt je Eintrag ein Feld
``lizenz_quelle`` — und bis zur Lizenzprüfung vom 18.08.2026 trug jede es anders:
``backbone`` kannte drei feste Vokabeln und verglich exakt gegen
:data:`QUELLE_MODELLKARTE`, die beiden anderen trugen freien Text mit Datum und URL.

Der Prüfbericht (``docs/LIZENZPRUEFUNG_2026-08-18.md``, Abschnitt 5) nennt den Schaden:
Ein Vermerk ``"geprueft 2026-08-18 (<url>)"`` war für die Prüflogik **kein** Beleg und
wurde als „Lizenzangabe NICHT geprüft" weitergemeldet — obwohl er das Gegenteil sagt. Ein
Beleg, den die Prüflogik nicht als Beleg erkennt, ist kein Beleg.

Darum steht die Vokabel jetzt an **einer** Stelle, und die drei Registries lesen sie von
hier. Ein eigenes Modul und nicht ``backbone`` als Quelle: Ein Tiefenschätzer hat mit der
Backbone-Registry sachlich nichts zu tun, und eine Abhängigkeit dorthin wäre eine
erfundene. Die Lizenzherkunft ist die einzige Sache, die alle drei teilen — also ist sie
das Modul.

Zwei Formen, ein Begriff
------------------------
Ein Beleg ist entweder das Schlagwort :data:`QUELLE_MODELLKARTE` oder — reicher — ein
Vermerk der Form ``"geprueft <datum> (<url>)"``. Das Schlagwort sagt *dass* geprüft
wurde, der Vermerk sagt **wogegen** und **wann**. Beides gilt, weil der Bestand beides
enthält; neue Einträge sollen die reiche Form nehmen.

Was dieses Modul NICHT tut
--------------------------
Es beurteilt keine Lizenz. Ob ein Modell unter Regel 1 verwendet werden darf, entscheiden
die Registries; hier wird nur beantwortet, wie gut die Angabe **belegt** ist. Das sind
zwei verschiedene Fragen, und sie werden bewusst getrennt gehalten: Eine permissive
Lizenz aus einer Sekundärquelle bleibt eine Behauptung.

Abhängigkeiten: keine. Reine stdlib.
"""
from __future__ import annotations

#: Lizenz am Original geprüft (Modellkarte selbst gelesen).
QUELLE_MODELLKARTE = "modellkarte"

#: Lizenz nur über eine Sekundärquelle bekannt.
QUELLE_SEKUNDAER = "sekundaerquelle"

#: Lizenz NICHT geprüft. Vor produktivem Einsatz nachzuholen (Regel 1).
QUELLE_UNGEPRUEFT = "ungeprueft"

#: Vorsilbe für einen belegten Vermerk mit Quelle, z. B.
#: ``"geprueft 2026-08-18 (https://huggingface.co/…)"``.
QUELLE_GEPRUEFT_PRAEFIX = "geprueft "

#: Vorsilbe beider Hinweistexte aus :func:`hinweis_zur_herkunft`. Steht hier, damit ein
#: Aufrufer (und ein Test) die Herkunfts-Auflage von den Lizenz-Auflagen unterscheiden
#: kann, ohne auf das Wort „geprüft" zu suchen — das steht auch in Auflagen, die mit der
#: Herkunft nichts zu tun haben.
HERKUNFT_HINWEIS_PRAEFIX = "Lizenzangabe"


#: Die vier Lizenzfamilien, die Regel 1 wörtlich nennt.
#:
#: `CLAUDE.md`: *„Alles, was in das ausgelieferte Produkt eingeht, ist MIT, Apache-2.0,
#: BSD oder MPL-2.0."* Die Liste steht hier und nicht in einer der Registries, weil alle
#: drei sie brauchen und drei Kopien derselben Regel früher oder später auseinanderlaufen.
PERMISSIVE_LIZENZEN = ("Apache-2.0", "MIT", "BSD-3-Clause", "BSD-2-Clause", "MPL-2.0")


def ist_permissiv(lizenz) -> bool:
    """Ist das eine der vier Lizenzfamilien aus Regel 1? Buchstäblich, ohne Auslegung.

    **Nicht dasselbe wie „darf verwendet werden".** Eine Lizenz kann kommerzielle Nutzung
    erlauben und trotzdem nicht permissiv sein — CreativeML OpenRAIL-M und die Stability
    Community License sind genau das. Regel 1 verlangt permissiv, nicht bloss erlaubt;
    :mod:`aiimaging.einbetter` begründet mit exakt diesem Satz den Ausschluss von DINOv3.

    Diese Funktion trifft die Entscheidung nicht, sie macht sie **sichtbar**. Siehe
    :func:`regel_1_spannung`.
    """
    return str(lizenz) in PERMISSIVE_LIZENZEN


def regel_1_spannung(name: str, lizenz, zulaessig: bool) -> str | None:
    """Ein Satz, wenn ein Eintrag zugelassen ist, ohne permissiv zu sein — sonst ``None``.

    **Der Befund, aus dem das entstand** (18.08.2026, Aufräumen nach der Lizenzprüfung):
    Zwei Registries desselben Projekts wenden Regel 1 **verschieden streng** an.

    * :mod:`aiimaging.einbetter` schliesst **DINOv3** aus. Kommerzielle Nutzung wäre
      erlaubt; die Begründung im Code lautet wörtlich *„Regel 1 verlangt permissiv, nicht
      bloss erlaubt"*.
    * :mod:`aiimaging.backbone` lässt **sdxl-juggernaut** (CreativeML OpenRAIL-M) und
      **sd35-large** (Stability AI Community License) zu — beide erlauben kommerzielle
      Nutzung, beide sind nicht permissiv. Dieselbe Klasse von Lizenz, entgegengesetztes
      Urteil.

    Das ist keine Auslegungsfrage, sondern eine **Uneinheitlichkeit im Vollzug**. Sie hier
    aufzulösen wäre falsch: Ein Ausschluss nähme dem Projekt den Rückfall-Backbone, und
    das ist ein Owner-Entscheid, keine Aufräumarbeit. Ihn stillschweigend stehen zu lassen
    wäre aber auch falsch — darum steht er ab jetzt **in jeder Antwort von
    ``pruefe_lizenz``**, statt nur in einem Bericht.

    Returns:
        Den Spannungssatz, oder ``None``, wenn kein Widerspruch besteht.
    """
    if not zulaessig or ist_permissiv(lizenz):
        return None
    return (
        f"REGEL-1-SPANNUNG, Owner-Entscheid ausstehend: {name} gilt als zulässig, aber "
        f"'{lizenz}' ist keine der vier Lizenzen, die Regel 1 nennt (MIT, Apache-2.0, "
        f"BSD, MPL-2.0). Kommerzielle Nutzung ist erlaubt — Regel 1 verlangt aber "
        f"permissiv, nicht bloss erlaubt, und mit genau dieser Begründung schliesst "
        f"aiimaging.einbetter das Modell DINOv3 aus. Dieselbe Klasse von Lizenz, "
        f"entgegengesetztes Urteil. Aufgelöst wird das nicht hier: Ein Ausschluss nähme "
        f"dem Projekt eine Fähigkeit, und das entscheidet der Owner."
    )


def ist_belegt(lizenz_quelle) -> bool:
    """Ist diese Herkunftsangabe ein Beleg am Original?

    Belegt ist :data:`QUELLE_MODELLKARTE` oder ein Vermerk der Form
    ``"geprueft <datum> (<url>)"``. Eine Sekundärquelle und ``ungeprueft`` sind es nicht.

    Warum nicht auf Gleichheit mit einer Vokabel geprüft wird, steht im Modulkopf: Die
    Lizenzprüfung vom 18.08.2026 trug URLs ein, und ein Vergleich auf Gleichheit meldete
    die frisch belegten Einträge weiter als ungeprüft.

    Ein Wert, der kein Text ist (``None``, eine Zahl), gilt als **nicht** belegt statt
    einen Fehler zu werfen: Die zurückhaltende Antwort ist hier die richtige — eine
    kaputte Angabe ist kein Beleg.
    """
    if not isinstance(lizenz_quelle, str):
        return False
    return (lizenz_quelle == QUELLE_MODELLKARTE
            or lizenz_quelle.startswith(QUELLE_GEPRUEFT_PRAEFIX))


def hinweis_zur_herkunft(lizenz_quelle) -> str | None:
    """Der Satz, der eine unbelegte Lizenzangabe als solche benennt — oder ``None``.

    ``None`` heisst: belegt, es gibt nichts anzumerken. Sonst ein Text, der zwischen den
    beiden Stufen unterscheidet, weil der Unterschied zählt — eine Sekundärquelle ist
    schlechter als die Modellkarte und besser als gar nichts.

    Der Text beginnt in beiden Fällen mit :data:`HERKUNFT_HINWEIS_PRAEFIX`, damit
    Aufrufer die Herkunfts-Auflage von einer Lizenz-Auflage unterscheiden können.
    """
    if ist_belegt(lizenz_quelle):
        return None
    if lizenz_quelle == QUELLE_SEKUNDAER:
        return f"{HERKUNFT_HINWEIS_PRAEFIX} nur über eine Sekundärquelle bekannt"
    return f"{HERKUNFT_HINWEIS_PRAEFIX} NICHT geprüft"


__all__ = [
    "PERMISSIVE_LIZENZEN", "ist_permissiv", "regel_1_spannung",
    "HERKUNFT_HINWEIS_PRAEFIX",
    "QUELLE_GEPRUEFT_PRAEFIX", "QUELLE_MODELLKARTE", "QUELLE_SEKUNDAER",
    "QUELLE_UNGEPRUEFT",
    "hinweis_zur_herkunft", "ist_belegt",
]
