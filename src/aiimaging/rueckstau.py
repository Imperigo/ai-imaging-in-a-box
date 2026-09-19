"""Der Rückstau über **zwei** Ablagen — weil eine Zahl aus einer Ablage eine halbe ist.

**Der Anlass ist ein eigener Fehler, und er steht hier, damit er nicht wiederkehrt.**
Am 19.09.2026 galt `auf-20260906-80` in diesem Baum als unbeantwortet. Er war zweimal
beantwortet — im anderen Repo. Daraus wurde ein Vorwurf («dreizehn Tage unbemerkt»),
und der Vorwurf war falsch. Gemessen am selben Tag: **sieben von 28** hier offenen
Aufträgen tragen drüben eine Antwort.

Dieselbe Klasse wie der Befund, den der Absender uns schon einmal geschrieben hat:
*zugestellt an die Adresse, nicht an den Adressaten.* Eine Zählung, die nur ihr eigenes
Verzeichnis kennt, misst genau das nicht.

**Owner-Entscheid 19.09.2026:** Es bleiben zwei Ablagen. Ein Umzug bräche, was läuft —
die Werkzeuge liegen hier, der Verkehr läuft drüben. Statt eines Umzugs zählt dieses
Modul beide zusammen.

Drei Eigenschaften, und jede hat ihren Grund:

1. **Zugeordnet wird über die Kennung, nie über die Nummer.** Die erste Fassung dieser
   Messung lief über die laufende Nummer und meldete 15 Treffer statt 7 — acht davon
   Dateien einer anderen Nummernreihe (`erg-20260906-51` beantwortet B48, nicht
   `auf-20260826-51`). *Eine Nummer ist keine Kennung, solange zwei Reihen sie vergeben.*
2. **Die Kennung zählt auch im Text**, nicht nur im Dateinamen. Genau so lagen die
   Antworten, die übersehen wurden: unter `erg-<datum>-<nr>-<titel>.md`.
3. **Ein fehlender Fremdbaum wird benannt, nicht verschwiegen.** Der `cloud`-Worker hat
   ihn nicht. Meldete das Werkzeug dort stillschweigend «alles offen», erzeugte es
   denselben Vorwurf, gegen den es gebaut ist. *Was es nicht sehen kann, nennt es beim
   Namen.*
"""
from __future__ import annotations

import re
from pathlib import Path

from . import auftrag as _auftrag

#: Wo im Fremdbaum **Antworten** liegen — und zwar nur dort.
#:
#: **Die erste Fassung war weiter und hat sich sofort geirrt.** Sie las auch
#: ``auftraege/von-kosmovis`` und ``kosmo-orbit/docs/auftraege-kosmovis`` und meldete
#: `auf-20260827-61` als beantwortet. Die Kennung stand dort in `auf-20260827-62.md` —
#: in einem **Auftrag**, der auf sie verweist, nicht in einer Antwort.
#:
#: *Erwähnt zu werden ist keine Antwort.* Ein Ordner voller Auftragsblätter beantwortet
#: nichts; er stellt Fragen. Gemessen: mit den weiten Verzeichnissen 10 Treffer, mit
#: diesem einen 9 — und der eine Unterschied war der Fehlbefund.
FREMD_VERZEICHNISSE = (
    "auftraege/ergebnisse",
)

#: Nur diese Endungen werden gelesen — ein Bildordner im Fremdbaum soll nicht gegrept werden.
FREMD_ENDUNGEN = (".json", ".md")

#: Der Vorbehalt, wenn der Fremdbaum fehlt. Wörtlich geprüft in `test_rueckstau.py`.
VORBEHALT_OHNE_FREMDBAUM = (
    "Der zweite Ablagebaum wurde NICHT gesehen. Diese Zahlen kennen nur die hiesige "
    "Ablage; ein Auftrag kann drueben beantwortet sein, ohne dass es hier auffaellt."
)


def _fremde_texte(fremd_wurzel: Path) -> list[str]:
    """Jede Antwortdatei des Fremdbaums einmal als Text — Inhalt, nicht nur Name."""
    texte: list[str] = []
    for rel in FREMD_VERZEICHNISSE:
        verz = fremd_wurzel / rel
        if not verz.is_dir():
            continue
        for pfad in sorted(verz.iterdir()):
            if pfad.is_file() and pfad.suffix in FREMD_ENDUNGEN:
                try:
                    texte.append(pfad.name + "\n" + pfad.read_text(encoding="utf-8", errors="replace"))
                except OSError:
                    continue
    return texte


def _kennung_kommt_vor(kennung: str, texte: list[str]) -> bool:
    """Die ganze Kennung, an einer Wortgrenze — nie die blosse Nummer.

    `\\b` allein genügt nicht: In `auf-20260826-510` endet `auf-20260826-51` vor einer
    Ziffer, und eine Ziffer ist keine Wortgrenze. Darum die ausdrückliche Nachschau.
    """
    muster = re.compile(re.escape(kennung) + r"(?![0-9-])")
    return any(muster.search(t) for t in texte)


def rueckstau(repo_wurzel, fremd_wurzel=None) -> dict:
    """Was hier offen ist, und was davon drüben schon beantwortet wurde.

    Args:
        repo_wurzel: Dieses Repo.
        fremd_wurzel: Der zweite Ablagebaum. ``None`` oder nicht vorhanden ist **kein
            Fehler** — dann steht der Vorbehalt im Bericht.

    Returns:
        ``offen`` (alles, was hier als unerledigt gilt), ``anderswo_beantwortet``,
        ``wirklich_offen``, ``fremdbaum_gesehen`` und ``vorbehalt``.
    """
    repo_wurzel = Path(repo_wurzel)
    offen = [a["auftrag_id"] for a in _auftrag.unerledigt(repo_wurzel)]

    fremd = Path(fremd_wurzel) if fremd_wurzel else None
    gesehen = bool(fremd and any((fremd / rel).is_dir() for rel in FREMD_VERZEICHNISSE))
    texte = _fremde_texte(fremd) if gesehen else []

    anderswo = [k for k in offen if _kennung_kommt_vor(k, texte)]
    return {
        "offen": offen,
        "anderswo_beantwortet": anderswo,
        "wirklich_offen": [k for k in offen if k not in set(anderswo)],
        "fremdbaum_gesehen": gesehen,
        "fremdbaum": str(fremd) if fremd else "",
        "vorbehalt": "" if gesehen else VORBEHALT_OHNE_FREMDBAUM,
    }
