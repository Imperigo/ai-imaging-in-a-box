# Zwei Entscheidungen, gemessen vorbereitet — und eine davon ist noch nicht dran

**02.09.2026 · Vorlage für den Owner. Keine Empfehlung ohne Zahlen, keine Zahl ohne
ihren Vorbehalt.**

---

## Wozu dieses Blatt

Zwei Fragen sind in den letzten beiden Tagen aus Messungen herausgefallen, und beide sind
**Entscheidungen und keine Messungen**: Welcher der beiden Fehler schwerer wiegt, und was
einen Standpunkt besser macht, kann kein Werkzeug ausrechnen.

Sie stehen hier zusammen, damit sie an einem Ort entschieden werden können. *Was der Owner
erst zusammensuchen muss, existiert nicht.*

**Eine der beiden ist heute schon entscheidbar, die andere ausdrücklich nicht** — und der
Unterschied ist der wichtigste Satz dieses Blatts.

---

## Entscheidung A · Die dritte Grösse für die Standpunktwahl — **heute entscheidbar**

### Die Frage in einem Satz

Die Wahl der drei Kamerastandpunkte ruht faktisch auf **einer** Grösse. Soll eine zweite
dazu — und wenn ja, welche?

### Was gemessen ist

`tools/studie_standpunkte.py`, sechs Bauformen, ohne GPU. Von zwölf Richtungen fallen die
vier frontalen immer heraus (keine zweite Fassade). Über die **acht** übrigen:

| Befund | Zahl |
|---|---|
| verschiedene Gütewerte über acht Standpunkte | **höchstens 2**, auf einem Würfel **1** |
| Kombinationen mit demselben Bestwert (von 56) | **4 bis 16** |
| Formen, in denen `flaechenanteil` den Sieger entscheidet | **1 von 6** |
| Spanne des Flächenanteils | 1,07 × (Würfel) bis 2,25 × (Riegel) |

Beim Riegel zeigt der Flächenanteil sogar in die andere Richtung: Der Sieger trägt 92 %,
die Unterlegenen 100 % — `zweite_fassade` überstimmt ihn.

> **Die Wahl trifft `zweite_fassade` allein.** Der Flächenanteil ist nicht schädlich, aber
> er entscheidet fast nie; und wo mehrere gleich gut sind, wählt die Reihenfolge der Liste.
> *Genau diesen Vorwurf macht die Güte dem Füllgrad, eine Ebene tiefer.*

### Die Möglichkeiten

| | was es kostet | was es erlaubt |
|---|---|---|
| **1 · Nichts ändern** | nichts | Die Wahl bleibt, wie sie ist — und die Meldung sagt seit gestern ehrlich, dass sie eine von vielen ist. |
| **2 · Eine dritte Grösse aufnehmen** | Sie muss **erfunden und dann gemessen** werden: Was macht einen Standpunkt besser? Verdeckung? Himmelsanteil? Sonnenstand? Ein halber Tag Bau, dazu eine Messreihe. | Eine Rangfolge, die wirklich ordnet — heute teilt sie in zwei Haufen. |
| **3 · Die Wahl offenlegen statt schärfen** | wenig — die Zahlen liegen | Der Betreiber bekommt die vier bis sechzehn gleichwertigen Sätze **zur Auswahl** statt einen zugewiesen. Ehrlicher, aber es verschiebt die Entscheidung an ihn. |

### Meine Empfehlung: **1, mit einer Bedingung**

Nichts ändern — **aber erst, wenn ein echtes Gebäude gemessen ist.** Alles oben ist an
sechs Quadern gerechnet. Ein Bau mit Vor- und Rücksprüngen hat mehr als zwei
Silhouettenklassen, und dann ordnet die Güte womöglich von selbst.

*Eine dritte Grösse zu erfinden, bevor feststeht, ob die zweite an einem echten Bau
versagt, hiesse ein Problem zu lösen, das nur Quader haben.*

**Was dafür nötig ist:** ein Standpunktsatz über ein echtes Modell — dieselbe Datei, an der
die HomeStation gestern die Achse gemessen hat. Das ist eine Zeile in einem bestehenden
Auftrag und kein neuer.

---

## Entscheidung B · Die richtungsabhängige ρ-Schwelle — **heute NICHT entscheidbar**

### Die Frage in einem Satz

`PAAR_RHO_SCHWELLE = 0.80` gilt für alle Blickrichtungen. Soll sie für frontale und
diagonale Ansichten **verschieden** sein?

### Was gemessen ist

`docs/PAARSCHWELLEN_OBERGRENZE_2026-09-01.md`, vier Szenen × vier Richtungen × elf Fälle:

| Gruppe | höchster **schlechter** | niedrigster **guter** | fehlerfreies Fenster |
|---|---|---|---|
| frontal | 0.2568 | 0.3790 | (0.2568, 0.3790] |
| diagonal | 0.5311 | 0.9065 | (0.5311, 0.9065] |

**Die beiden Fenster überschneiden sich nicht.** Es gibt keine einzelne Schwelle, die
beide Gruppen fehlerfrei trennt — das folgt aus vier Zahlen und ist keine Frage der
Fallzahl.

Was `0.80` heute kostet:

| Gruppe | falsch bestanden | falsch gesperrt |
|---|---|---|
| frontal | **0** von 48 | **5** von 40 |
| diagonal | **0** von 48 | **0** von 40 |

Kein einziges falsches Bild kommt durch. Der ganze Preis sind fünf gute frontale Fälle,
und einer davon verfehlt die Schwelle um **0.0096**.

### Warum sie trotzdem nicht heute fällt

> **Alle acht Kurven melden `genuegt_als_kalibrierung: false.`**

Die Ist-Karten sind **gebaut, nicht geschätzt**. Der Fehler des Tiefenschätzers kommt darin
gar nicht vor — er trägt ein festes Ortsfeld, das allein 95,75 % der Varianz auf einem
leeren Bild erklärt. *Was hier scheitert, scheitert mit einem echten Schätzer erst recht;
was hier gelingt, ist damit nicht bestätigt.*

Eine Schwelle auf einer Obergrenze zu setzen wäre genau die **abgelesene Schwelle**, gegen
die dieses Projekt seit zwei Wochen antritt — nur mit mehr Nachkommastellen.

**Was fehlt:** `auf-20260827-61`, Rang 3 bei der HomeStation. Die Messwerkzeuge liegen
seit dem 27.08. bereit; es fehlen die Fälle unter Schätzerrauschen.

### Was jetzt schon feststeht, unabhängig von `auf-61`

Drei Sätze, die eine echte Messung nur **schärfen**, nicht umdrehen kann:

1. **Eine einzelne Schwelle wird beide Gruppen nicht fehlerfrei trennen.** Der Schätzer
   vergrössert den Abstand, er verkleinert ihn nicht.
2. **Die Richtung gehört in jede Fallzeile.** Steht sie nicht da, ist die Frage später
   nicht mehr zu beantworten — `auf-61` trägt die Auflage seit dem 28.08.
3. **`0.80` ist als richtungsblinde Wahl vertretbar**, solange der Preis fünf gesperrte
   gute frontale Fälle sind und **null** durchgelassene schlechte.

### Meine Empfehlung: **warten, und zwar erklärt**

Nicht entscheiden, bis `auf-61` zurück ist — *aber im Wissen, dass die Antwort
wahrscheinlich «richtungsabhängig» lautet.* Dieses Blatt ist die Vorlage dafür; wenn die
Messung kommt, sind es zwei Zahlen statt einer Untersuchung.

---

## Was passiert, wenn nichts entschieden wird

**Bei A:** nichts Schlimmes. Die Wahl bleibt, wie sie ist, und die Meldung sagt seit
gestern dazu, dass sie eine von vielen ist. Der Posten altert gut.

**Bei B:** auch nichts Schlimmes — **weil `0.80` in beiden Gruppen kein falsches Bild
durchlässt.** Der Preis läuft aber weiter auf: Jeder frontale Lauf, dessen ρ zwischen
0.3790 und 0.80 liegt, wird gesperrt, obwohl er gut ist. Wie oft das vorkommt, weiss
niemand — *auch das misst `auf-61`.*

---

## Anhang · Woher die Zahlen kommen

```
python tools/studie_standpunkte.py            # Entscheidung A
python tools/studie_ersatzkalibrierung.py     # Entscheidung B (Obergrenze)
```

`docs/STANDPUNKTE_2026-09-01.md` · `docs/PAARSCHWELLEN_OBERGRENZE_2026-09-01.md`
