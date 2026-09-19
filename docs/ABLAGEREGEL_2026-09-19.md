# Ablageregel — zwei Baeume bleiben, gezaehlt wird zusammen

**Owner-Entscheid 19.09.2026.** Vorgelegt waren drei Wege: alles hierher, alles
hinueber, oder zwei Baeume mit einer klaren Regel. Gewaehlt ist der dritte.

**Dieses Blatt ist ein Nachtrag, kein Ersatz.** Die aeltere und gruendlichere Regel ist
`Architektur-Cosmos/kosmo-orbit/docs/KONVENTION-AUFTRAGSPIPELINE.md` (06.09.2026) — sie
beschreibt die drei Auftragssysteme, die Uebertragungsstelle (§5) und was ein Auftrag
tragen muss, um zustellbar zu sein (§6). Wo sie etwas regelt, gilt sie. Hier steht nur,
was am 19.09.2026 dazugekommen ist.

---

## 1 · Warum nicht umgezogen wird

Beide Baeume sind in Betrieb, und jeder haelt etwas, das der andere nicht hat:

| | `ai-imaging-in-a-box/auftraege/` | `Architektur-Cosmos/auftraege/` |
|---|---|---|
| Vertrag und Werkzeuge | `auftrag.py`, `einbau.py`, `rueckstau.py` | — |
| Verkehr in den letzten drei Wochen | letzte Lieferung der Gegenstelle 28.08.2026 | Lieferung am 18.09.2026 |
| Oeffentlich | ja | nein |

*Ein Umzug in die eine Richtung liesse die Werkzeuge zurueck, in die andere den Verkehr.
Beides waere teurer als die Regel unten.*

---

## 2 · Die Regel

1. **Ein Auftrag bleibt, wo sein Adressat ihn liest.** Umgelegt wird nichts, was schon
   liegt. Die Uebertragungsstelle aus §5 der Konvention bleibt der einzige Weg, auf dem
   ein Blatt den Baum wechselt — und sie hinterlaesst einen Vermerk, woher es kam.
2. **Antworten gehoeren in `auftraege/ergebnisse/`** des Baums, in dem der Auftrag
   gestellt wurde. Nur dieser Ordner gilt als Antwortort. *Erwaehnt zu werden ist keine
   Antwort* — ein Auftragsordner stellt Fragen, er beantwortet keine.
3. **Gezaehlt wird ueber beide Baeume, nie ueber einen.** `tools/rueckstau.py` tut das.
   Eine Zahl aus einem Baum ist eine halbe Auskunft und darf nicht als Rueckstand
   ausgegeben werden.
4. **Wer den zweiten Baum nicht hat, bekommt den Vorbehalt mitgeliefert.** Das Werkzeug
   meldet in der ersten Zeile, dass es nur die eine Ablage gesehen hat. Ohne diesen Satz
   entsteht genau der Vorwurf, gegen den die Regel gebaut ist.

---

## 3 · Was den Anlass gab

Am 19.09.2026 galt `auf-20260906-80` hier als unbeantwortet, weil in diesem Baum keine
Antwort lag. Er war zweimal beantwortet — am 06./07.09. und vollstaendig am 17.09., im
anderen Repo. Daraus wurde ein Vorwurf («dreizehn Tage unbemerkt»), und der Vorwurf war
falsch.

Gemessen am selben Tag, mit dem neuen Werkzeug:

```
python tools/rueckstau.py
  OFFEN NACH HAUSREGEL: 33
  DRUEBEN BEANTWORTET :  9
  WIRKLICH OFFEN      : 24
```

*Neun von 33 — fast jeder vierte Auftrag, den dieses Repo als offen fuehrte, war es
nicht.*

---

## 4 · Zwei Fallen, beide am selben Tag getreten

**Eine Nummer ist keine Kennung.** Die erste Zuordnung lief ueber die laufende Nummer
und meldete 15 Treffer statt 7. Acht davon waren Dateien einer anderen Nummernreihe —
`erg-20260906-51` beantwortet B48, nicht `auf-20260826-51`. Zugeordnet wird ueber die
ganze Kennung, und `tests/test_rueckstau.py` haelt das fest.

**Erwaehnt zu werden ist keine Antwort.** Die erste Fassung des Werkzeugs las auch die
Auftragsordner des Fremdbaums und meldete `auf-20260827-61` als beantwortet — die
Kennung stand in `auf-20260827-62.md`, einem Auftrag, der auf sie verweist. Mit den
weiten Verzeichnissen 10 Treffer, mit dem einen richtigen 9.

---

## 5 · Was offen bleibt

Die Konvention drueben kennt diesen Nachtrag noch nicht. Ein Verweis von dort hierher
fehlt — und genau das ist die Fehlerklasse, die dieses Blatt behandelt. Er wird
nachgetragen.
