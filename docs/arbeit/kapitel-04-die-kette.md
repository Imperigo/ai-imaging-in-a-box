# 4 · Die Kette: aus vier Knoten wurden sechs

> **Stand 19.09.2026 — Entwurf.** Sechstes geschriebenes Kapitel.
> **Alle Zeitangaben sind am 19.09.2026 gemessen**, nicht zitiert: `tools/beweis/05_der_graph.py`
> und `tools/beweis/23_speicher_am_produktivweg.py`, beide für dieses Kapitel gefahren.
> **Der Kapitelname der Gliederung ist überholt.** Dort heisst es «vier Knoten»; seit dem
> 19.09.2026 sind es sechs.

---

## 4.1 Warum überhaupt ein Graph

Ein Bild entsteht hier nicht in einem Schritt, sondern in mehreren, und die Schritte sind
**verschieden teuer**. Aus dem Gebäudemodell eine Geometrie zu rechnen, kostet Sekunden
und einen Aufruf eines fremden Programms. Ein Wort im Prompt zu ändern kostet nichts.

Wer beides in **eine** gerade Abfolge legt, zahlt für die Wortänderung den Preis der
Geometrie. Genau das ist die Arbeitsweise, um die es geht: Eine Architektin ändert nicht
das Gebäude, sondern die Stimmung — «Abendlicht» statt «Mittagslicht» —, und zwar zehnmal
hintereinander.

Die Antwort darauf ist ein **gerichteter Graph mit Zwischenspeicher**: Jeder Schritt ist
ein Knoten, jeder Knoten kennt seine Eingänge, und was sich nicht geändert hat, wird nicht
noch einmal gerechnet.

> **Die Frage ist nicht, wie schnell ein Bild entsteht, sondern wie schnell das
> *zweite*.**

---

## 4.2 Die sechs Knoten

| Knoten | Was er tut | Seit |
|---|---|---|
| `geometrie` | Aus der Gebäudedatei eine Geometrie für das Rendern machen | Anfang |
| `multipass` | Aus der Geometrie die Bildebenen rechnen — darunter die Tiefenkarte | Anfang |
| `render` | Aus Tiefenkarte und Prompt ein Bild erzeugen | Anfang |
| `qa` | Prüfen, ob das Bild der Geometrie folgt | Anfang |
| `bildquelle` | Ein **vorhandenes** Bild in die Rechnung geben | 19.09.2026 |
| `nachrender` | Auf einem vorhandenen Bild weiterrechnen, statt bei null anzufangen | 19.09.2026 |

Die ersten vier bilden eine Kette: Geometrie → Bildebenen → Bild → Prüfung. Vier Knoten,
vier Kanten, eine eindeutige Reihenfolge.

**Die letzten beiden sind am 19.09.2026 dazugekommen** und ändern die Form des Graphen:
Ein Bild kann jetzt auch **von aussen** hereinkommen — aus einer Datei, in die jemand
hineingezeichnet hat. Damit hat der Graph eine zweite Wurzel, die nicht im Gebäudemodell
liegt.

*Das ist keine Erweiterung um der Vollständigkeit willen.* Es ist die technische Form
eines Entscheids: Über der geprüften Geometrie liegt eine zweite Stufe, auf der von Hand
oder mit KI an den Bildpunkten gearbeitet wird. Was dort entsteht, trägt **kein eigenes**
Geometrie-Urteil mehr — wohl aber das seiner Unterlage.

---

## 4.3 Was der Zwischenspeicher leistet, gemessen

Vier Läufe, je gezählt, wie viele der vier Knoten wirklich gerechnet haben und wie viele
aus dem Speicher kamen:

| Lauf | Was sich änderte | gerechnet | aus dem Speicher |
|---|---|---|---|
| 1 | — (erster Durchlauf) | **4** | 0 |
| 2 | **nur der Prompt** | 2 | **2** |
| 3 | gar nichts | **0** | **4** |
| 4 | **die Geometrie** | **4** | 0 |

Drei Aussagen stecken darin, und jede ist eine eigene:

**Lauf 2 ist der Zweck der ganzen Konstruktion.** Ein geändertes Wort lässt die beiden
Geometriestufen unberührt; nur Bild und Prüfung laufen neu.

**Lauf 3 zeigt, dass der Speicher wirklich greift** und nicht bloss selten zuschlägt. Wenn
sich nichts ändert, wird nichts gerechnet.

**Lauf 4 ist der wichtigere Nachweis.** Ändert sich die Geometrie, fällt **alles
dahinter** — auch das Bild, auch die Prüfung. Ein Speicher, der zu viel behält, ist
gefährlicher als gar keiner: Er liefert dann ein Bild zu einem Gebäude, das es nicht mehr
gibt, und niemand sieht es ihm an.

---

## 4.4 Der Einwand, und die Messung dagegen

**Der Einwand ist berechtigt und stand lange unwidersprochen:** Dieser Graph läuft nicht am
Produktivweg. Was in der laufenden Software Aufträge abarbeitet, fährt die Stufen als
gerade Abfolge; `kette.baue_kette` hat ausserhalb seiner Tests und der Beweisskripte bis
heute **keinen Aufrufer**.

Daraus folgt aber nicht, was man zuerst vermutet. Die Frage ist nicht, ob der *Graph* dort
läuft, sondern ob der *Nutzen* dort ankommt — und das ist messbar. Dieselben vier Läufe,
gestellt an den echten Produktivweg, mit gezählten Aufrufen des externen Renderprogramms:

| Lauf | Geometrie | Verhalten | Dauer |
|---|---|---|---|
| 1 | A | **gerechnet** | 2,42 s |
| 2 | A | aus dem Speicher | **0,27 s** |
| 3 | A | aus dem Speicher | **0,19 s** |
| 4 | **B** | **gerechnet** | 2,32 s |

In den Läufen 2 und 3 wird das externe Renderprogramm **kein einziges Mal** gestartet. Der
Faktor liegt bei rund **neun**, und er ist nicht geschätzt, sondern aus den vier Zeiten
gerechnet.

**Der Grund, warum das kein Zufall ist:** Der Produktivweg prüft die Gültigkeit seines
Speichers nicht mit einer eigenen Regel, sondern mit **derselben** wie der Graph. Beide
fragen dieselbe Stelle, welche Dateien ein Zwischenergebnis mitbringen muss.

> *Damit trennt sich «gebaut, aber nicht im Betrieb» von «der Nutzen fehlt» — und nur das
> Erste stimmt.*

Das ist eine kleinere Behauptung als die ursprüngliche, und sie ist belegt. Die grössere
wäre bequemer und falsch.

---

## 4.5 Warum die Reihenfolge Bedeutung trägt

Ein Knoten kennt seine Eingänge **als Reihenfolge**, nicht als Menge. Beim Prüfknoten
heisst das: Eingang 0 ist das Soll — die Geometrie —, Eingang 1 ist das Ist — das erzeugte
Bild.

Das klingt nach einer Feinheit und ist keine. Wer die beiden vertauscht, bekommt keine
Fehlermeldung, sondern **ein Ergebnis**: Die Prüfung misst dann das Bild gegen sich selbst
oder die Geometrie gegen die Geometrie, und beides sieht nach einer bestandenen Prüfung
aus.

*Es ist derselbe Fehlertyp, der dieses Projekt an mehreren Stellen beschäftigt hat: nicht
ein Absturz, sondern ein Ergebnis, das falsch ist und richtig aussieht.*

---

## 4.6 Grenzen dieses Kapitels

**Erstens: Der Graph ist am Produktivweg weiterhin nicht im Einsatz.** Gemessen ist, dass
der Nutzen dort trotzdem ankommt — nicht, dass die beiden Wege dasselbe tun. Sie teilen
die Regel für die Gültigkeit des Speichers; sie teilen nicht die Form. Ein Unterschied im
Verhalten wäre heute nicht auszuschliessen.

**Zweitens: Die Zeiten stammen von einer Maschine.** 2,42 gegen 0,27 Sekunden sind hier
gemessen, auf einer Maschine ohne Grafikkarte, mit einer kleinen Szene. Der Faktor wird
mit der Szenengrösse wachsen — behauptet wird das nicht, gemessen ist es nicht.

**Drittens, und es ist die relevanteste:** Die beiden neuen Knoten sind **am selben Tag
gebaut wie dieses Kapitel**. Sie sind geprüft — auch gegen die Gegenrichtung, also dagegen,
dass ein Vorbehalt beim Weiterrechnen verlorengeht —, aber sie haben noch nie ein echtes
Bildmodell gesehen. Ob ein hineingezeichnetes Bild am Vorgabe-Modell überhaupt ankommt,
ist **nicht gemessen**; bei einem anderen Modell ist am 18.08.2026 gemessen worden, dass es
still verschwindet. Die Messung ist bestellt.

---

## Belegstellen

| Abschnitt | Im Repo |
|---|---|
| 4.2 Die sechs Knoten | `src/aiimaging/kette.py`, Konstanten `ART_*` |
| 4.3 Die vier Läufe | `tools/beweis/05_der_graph.py`, gefahren am 19.09.2026 |
| 4.4 Der Produktivweg | `tools/beweis/23_speicher_am_produktivweg.py`, gefahren am 19.09.2026 |
| 4.4 Dieselbe Speicherregel | `aiimaging.abholer` ruft `kette._cache_maengel` und `kette.BEDARF` |
| 4.5 Reihenfolge als Bedeutung | `kette.baue_kette`, Eingänge des Prüfknotens |
| 4.6 Die offene Messung | `auftraege/offen/auf-20260919-123.json` |
