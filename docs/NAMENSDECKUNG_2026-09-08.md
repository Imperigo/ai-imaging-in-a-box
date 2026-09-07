# Sehen Boxseite und Bildseite dieselben Namen?

**08.09.2026** · gemessen in dieser Umgebung, **ohne GPU und ohne Blender**

---

## Die Frage, und warum sie über einen Bau entschieden hat

Seit dem 07.09.2026 erkennt `gelaendeform` Gelände an der **Gestalt**, wenn der Name es
nicht trägt. Das hilft der **Boxseite** (`glbbox.bauwerksbox`).

Die **Bildseite** (`maske.bauwerksmaske`) benutzt dieselbe Namensregel und kann diesen
Ausweg nicht nehmen: Sie bekommt eine flache Bildpunktliste und eine Farbtabelle — **keine
Geometrie, keine Bildbreite, keine Positionen.** Ein Formmerkmal ist von dort aus nicht
rechenbar.

Übertragen liesse sich das **Ergebnis**: die Namen, die die Form als Gelände erkannt hat.
Das trägt genau dann, wenn beide Seiten dieselben Namen sehen — *und diese Studie ist die
Bedingung dafür, dass die Brücke überhaupt gebaut wurde.*

---

## Woher die Namen kommen

`blender_depth_stage._material_id_zuweisen` baut die Tabelle auf zwei Wegen, und sein
eigener Docstring nennt beide:

| `quelle` | Name aus | wann |
|---|---|---|
| `material` | `slot.material.name` | das Modell bringt Materialien mit |
| `objekt` | `obj.name` | das Mesh trägt **kein** Material — *«der Normalfall der aktuellen Kette»* |

Die Boxseite liest immer glTF-**Knotennamen**.

---

## Die Messung

```
=== ein Gelaendekoerper
  Knoten: ['IfcCovering_Sub-Division:1', 'IfcWall_Aussenwand:12']
  Von der FORM als Gelaende erkannt: ['IfcCovering_Sub-Division:1']
  Fall                   quelle     Deckung  Tabellennamen
  material               material        0%  0/1 Gelaende-Eintraege, verfehlt: ['Volumen']
  objekt                 objekt        100%  1/1 Gelaende-Eintraege
  objekt_mit_dubletten   objekt        100%  1/1 Gelaende-Eintraege

=== geteiltes Gelaende (4 Knoten)
  Knoten: ['IfcCovering_Sub-Division:1', 'IfcWall_Aussenwand:12']
  Von der FORM als Gelaende erkannt: ['IfcCovering_Sub-Division:1']
  Fall                   quelle     Deckung  Tabellennamen
  material               material        0%  0/1 Gelaende-Eintraege, verfehlt: ['Volumen']
  objekt                 objekt        100%  1/1 Gelaende-Eintraege
  objekt_mit_dubletten   objekt         25%  1/4 Gelaende-Eintraege, verfehlt: ['IfcCovering_Sub-Division:1.001', 'IfcCovering_Sub-Division:1.002', 'IfcCovering_Sub-Division:1.003']
```

---

## Drei Befunde

### 1 · Materialnamen und Knotennamen treffen sich nie — Deckung **0 %**

Die Bestandsmessung vom 06.09. (`auf-20260826-51`) nennt vier Namen: *Beton, Glas,
Volumen, mauerwerk.* Keiner davon ist ein Knotenname, und keiner wird je einer sein.

**Die Boxseite kann das Gelände in einer solchen Szene finden und die Bildseite nicht.**
Die Rahmung wäre richtig und die Maske trotzdem leer. Das ist keine Lücke, die sich
schliessen lässt — es ist eine Grenze, und sie steht seit heute als Warnung in der Maske.

*Ein Mangel, der benannt ist, ist kein Loch mehr.*

### 2 · Objektnamen decken sich vollständig — Deckung **100 %**

Im Normalfall unserer eigenen Kette (`ifc_to_glb_runner` überträgt keine Materialien)
vergibt Blender objektweise IDs, und die Namen passen. **Dort trägt die Brücke.**

### 3 · Blenders Dublettensuffix bricht sie — Deckung **25 %**

Der teuerste Befund, und er hat den Bau geändert. Blender vergibt Objektnamen
**eindeutig** und hängt bei einer Dublette `.001` an. Besteht das Gelände aus vier Knoten
desselben Namens, trägt die Tabelle vier Einträge — ein Vergleich auf Gleichheit trifft
nur den ersten.

> **Am echten Bestand sind es zwanzig `IfcCovering_Sub-Division`-Knoten.** Dort wären es
> **5 %**: Die Übertragung hätte einen von zwanzig Geländekörpern erwischt, und
> neunzehn Zwanzigstel des Bodens blieben in der Maske.

Deshalb vergleicht `maske.deckt_uebertragenen_namen` auf Gleichheit **oder** Gleichheit
nach Abzug des Suffixes. *Das ist keine weiche Regel:* Verglichen wird gegen ein Muster,
das Blender selbst nach einer festen Regel anhängt — drei Ziffern nach einem Punkt, sonst
nichts. Ein Wort mitten im Namen wäre etwas anderes, und davor warnt der Kommentar an
`UMFELD_KLASSEN` seit dem 01.09.

---

## Ein Fehler in der Messung selbst, und er stand fast im Dokument

Der erste Anlauf zählte, wie viele der von der Form erkannten **Namen** in der Tabelle
vorkommen. Beim geteilten Gelände ergab das **100 %** — und war falsch.

Die Maske arbeitet über **Tabelleneinträge**. Dort standen vier, und die Namensliste traf
einen. *Eine Deckung, die in die falsche Richtung misst, ist eine Zahl ohne Gegenstand* —
und sie hätte hier genau das Gegenteil dessen behauptet, was der Fall ist.

Gemessen wird seither über die Einträge, mit der bekannten Wahrheit je Eintrag.

---

## Was diese Studie **nicht** misst

**Sie läuft ohne Blender.** Sie baut die beiden Tabellenformen so nach, wie der Runner sie
laut seinem Quelltext baut. Das ist eine Aussage über die **Namensregel**, nicht über einen
Lauf.

Was Blender wirklich in `obj.name` schreibt — ob etwa der glTF-Import Namen kürzt oder
Sonderzeichen ersetzt —, kann nur ein Lauf auf der HomeStation sagen. *Bis dahin ist der
Objektfall gerechnet und nicht bestätigt.*

---

## Anhang · Woher die Zahlen kommen

```
python tools/studie_namensdeckung.py
python tools/studie_namensdeckung.py --json
```

`src/aiimaging/maske.py` (`deckt_uebertragenen_namen`, `gelaende_zusatz`) ·
`tests/test_studie_namensdeckung.py` · `docs/GELAENDEFORM_2026-09-07.md`
