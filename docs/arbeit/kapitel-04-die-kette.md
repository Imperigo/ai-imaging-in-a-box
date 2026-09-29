# 4 · Die Kette: aus vier Knoten wurden sechs

> **Stand 29.09.2026 — Entwurf** (geschrieben 19.09.2026, nachgezogen 21.09. und
> 29.09.2026). Sechstes geschriebenes Kapitel.
> **Alle Zeitangaben sind am 19.09.2026 gemessen**, nicht zitiert: `tools/beweis/05_der_graph.py`
> und `tools/beweis/23_speicher_am_produktivweg.py`, beide für dieses Kapitel gefahren.
> **Der Kapitelname der Gliederung ist überholt.** Dort heisst es «vier Knoten»; seit dem
> 19.09.2026 sind es sechs (am 29.09.2026 unverändert, `kette.ART_*`).
> **Nachgetragen am 29.09.2026:** der erste echte Lauf über die Mappe (4.2), ein
> abgeschalteter Speicher (4.3), und was seither im Render-Knoten rechnet — Vorgabemodell,
> ein stillgelegtes Modell, eine Forschungs-Ausnahme und die Ebenen (4.2, Nachtrag).
> Die dritte Grenze in 4.6 ist inzwischen **gemessen**, und sie fällt negativ aus.

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

### Nachtrag 29.09.2026: der erste echte Lauf, und was er über sich sagte

Am 22.09.2026 ist der Weg, den ein Mensch geht — Modelldatei → Mappe → wieder öffnen →
Kette fahren → Bild —, zum **ersten Mal am echten Gerät ganz durchgelaufen**
(`tools/beweis/31_der_weg_des_produkts.py --echt`, Auftrag `auf-20260922-137`). Der Weg
ruft über `arbeitsgang.rechne` genau diese Kette:

| Knoten | Dauer |
|---|---|
| `geometrie` | 0,0006 s |
| `multipass` | 2,24 s |
| `render` | 14,58 s — 8 gezählte Diffusionsschritte |
| `qa` | 0,75 s |
| **gesamt** | **17,6 s**, ein Bild vermerkt, nichts gescheitert |

**Die Prüfung hat dieses erste Bild abgewiesen, und zu Recht:** Score 0,000, die
Flächenüberschneidung bei 0,0096. Und der Lauf meldete selbst, dass er anders gerechnet
hatte als bestellt — bestellt `image_edit`, gerechnet `txt2img`, weil das Vorgabemodell kein
Eingangsbild annimmt (siehe 4.6). *Die Kette läuft; ein brauchbares Bild hat sie damit noch
nicht geliefert.*

### Nachtrag 29.09.2026: was im Render-Knoten rechnet

Der Knoten `render` hat seit dem Entwurf keinen neuen Eingang bekommen, aber das, was in ihm
rechnet, hat sich an vier Stellen verschoben. Weil das Kapitel über die Kette spricht und
nicht über Modelle, hier nur das, was die Form der Kette berührt:

1. **Das Vorgabemodell ist `z-image-turbo`** — in der Bibliothek seit dem 18.08.2026. Auf
   dem Weg der Bestellungen aus KosmoOrbit rechnete eine Bestellung **ohne Modellangabe**
   bis zum 29.09.2026 dagegen mit dem Bearbeitungsmodell `qwen-image-edit-2511`: 349 s je
   Bild statt rund 47 s, die Tiefe nur als Eingangsbild statt als Steuerung, und am Testbau
   ein erfundenes Haus statt des Quaders. Seit dem 29.09.2026 gilt dort der Wert aus dem
   Vertrag von KosmoOrbit, `z-image-turbo` (Einbau-Stand C34). Das Ergebnis nennt seither
   an der obersten Ebene, womit gerechnet wurde (`engine_used`, `engine_license`,
   `guidance_applied`; C35).
2. **`qwen-image-2512` ist stillgelegt** (Owner-Entscheid 29.09.2026). Es war das einzige
   weitere freie Modell mit eigener Tiefensteuerung; es hätte 48 GB gebraucht, und seine
   Steuerungsdatei war nach Herkunft, Lizenz und Format ungeklärt. **An der Tiefen-Naht
   bleibt damit genau ein freies Modell.** Eine Kette, die ihren wichtigsten Knoten nur
   mit einem einzigen Modell füllen kann, ist an dieser Stelle nicht austauschbar — das
   gehört zu den Grenzen dieses Kapitels.
3. **Eine Forschungs-Ausnahme, ohne Tiefensteuerung.** Seit dem 29.09.2026 darf
   Qwen-Image-2.1 am Heimrechner rechnen, nur mit Schalter und nie als Vorgabe (Kapitel 3,
   3.2). Laut Modellkarte hat es **kein** ControlNet. Ob die Geometrie über das
   Eingangsbild überhaupt ankommt, ist die eigentliche Frage — bei `qwen-image-edit-2511`
   kam sie nicht an (`auf-20260818-09/-10`). Bestellt als `auf-20260929-178`.
4. **Die Ebenen, Schritt 1** (Entscheid E124 von KosmoOrbit, bei uns gebaut am
   29.09.2026, C36). Eine Bestellung kann mit `render.passes` die Bildebenen anfordern, die
   der Knoten `multipass` ohnehin rechnet — `schoenbild`, `tiefe`, `material-id` oder
   `"alle"`. Sie kommen je Kamera als `<kamera>__<art>.png` zurück, mit einem Feld `ebenen`,
   das ihre Bedeutung in Zahlen trägt (Tiefe: Meter, nah hell, Rückrechnung;
   Material-ID: Tabelle und Nullfarbe). Ein Zwilling trägt seine eigenen Ebenen, nicht die
   seines Vorbilds. *Damit wird ein Zwischenergebnis der Kette zum ersten Mal selbst
   Lieferung.* Angezeigt wird es drüben erst nach einem echten Lauf; der steht aus
   (`auf-20260929-176`).

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

> **Nachtrag 29.09.2026 — zwei Befunde am Speicher, einer in jede Richtung.**
>
> **Zu wenig behalten (21.09.2026, behoben):** Auf dem Weg über die Mappe — dem Weg, den die
> Oberfläche benutzt — war der Speicher **gar nicht eingeschaltet**. Drei Läufe
> hintereinander ohne jede Änderung: `cache_treffer=0`, dreimal. Jeder Klick auf «Rechnen»
> rechnete Blender und das Bild neu, obwohl drei Beweise den Speicher belegten — nur eben
> nicht auf diesem Weg. Seither liegt er in der Mappe; nachgemessen ruft ein unveränderter
> zweiter Lauf Blender und das Bild **gar nicht** mehr auf, ein neuer Prompt kostet das Bild
> und nicht die Geometrie. *Eine Fähigkeit, die über den Weg des Produkts nicht erreichbar
> ist, gibt es für den Benutzer nicht.*
>
> **Zu viel behalten (23.09.2026, offen):** Genau der Fall, vor dem dieser Absatz warnt, ist
> eingetreten, nur nicht an der Geometrie, sondern am **Code**. Der Speicher der Mappe
> kennt den Codestand nicht. Als am 23.09.2026 die Führung des Bearbeitungsmodells
> repariert wurde, kam ein alter Knoten dieses Modells weiter **ohne Führung** aus dem
> Speicher. Angesagt, nicht behoben (`docs/PLAN.md`, Kern).

---

## 4.4 Der Einwand, und die Messung dagegen

**Der Einwand ist berechtigt und stand lange unwidersprochen:** Dieser Graph läuft nicht am
Produktivweg. Was in der laufenden Software Aufträge abarbeitet, fährt die Stufen als
gerade Abfolge; `kette.baue_kette` hatte ausserhalb seiner Tests und der Beweisskripte
lange **keinen Aufrufer**.

> **Nachtrag vom 21.09.2026 — der erste ist da, und er ist nicht der Abholer.**
> `aiimaging.arbeitsgang` ruft `baue_kette` und `fuehre_aus`, um für ein Projekt zu
> rechnen. Damit hat der Graph seinen ersten Aufrufer **im Produktcode** und nicht mehr
> nur in Tests.
>
> Der Einwand fällt damit nicht weg, er wird genauer: *Der Weg, auf dem heute Aufträge der
> Werkstatt abgearbeitet werden, benutzt den Graphen weiterhin nicht.*
>
> **Nachtrag vom 29.09.2026 — und daran hat auch die Knotenansicht nichts geändert.** Seit
> dem 24.09.2026 liegt eine Kopie der Knotenansicht von KosmoOrbit im Repo (`kosmovis/`),
> und über sie ist am selben Tag das erste Bild entstanden (`auf-20260924-164`: Graph
> Modell → Prompt → Render, «Ausführen», «Freigeben», Bild am Render-Knoten). Gerechnet hat
> es aber der **bestehende Abholer**, ohne zweite Rechenstrecke. Die Knoten, die man dort
> sieht, sind der Graph von KosmoOrbit, nicht `kette.baue_kette`. *Ein Bild über eine
> Knotenansicht ist nicht dasselbe wie ein Bild über den Graphen dieses Kapitels.*

### Und was «zwei Wege» wirklich hiess — nachgemessen am 21.09.2026

Hier stand zuerst: *«Es gibt jetzt zwei Wege statt einem, und zwei Wege sind nicht besser
als einer.»* Das war zu grob, und das Nachmessen hat etwas Genaueres und Unangenehmeres
ergeben.

**Die beiden Wege verdoppeln keinen Code.** Sie rufen dieselben drei Bibliotheksfunktionen
und benutzen dieselbe Regel dafür, wann ein Zwischenergebnis noch gilt. Das war schon
vorher so.

**Was sie unterschieden, war etwas anderes: was man bei ihnen bestellen kann.**

| | |
|---|---|
| Der Renderdienst nimmt an | **21** Angaben |
| Der alte Auftragsweg bestellt | **17** |
| Der Weg über den Graphen bestellte | **8** |

Elf Dinge waren über den Graphen nicht erreichbar — darunter **Sonnenstand,
Blickrichtung, Rahmung und Augenhöhe**, also genau das, was eine Architektin einstellen
will. Und der Graph ist der Weg, auf den eine Oberfläche aufsetzt.

> **Eine Fähigkeit, die der Renderdienst hat und die über einen der Wege nicht bestellbar
> ist, gibt es für jeden, der diesen Weg benutzt, nicht.**

Es war also nie «zwei Wege, die dasselbe tun». Es waren zwei Wege zu demselben Dienst, und
**der neuere konnte weniger.** Die Lücke ist geschlossen; zwei Wächter halten sie zu, und
sie messen gegen den Dienst selbst statt gegen eine Liste von Namen — *eine Liste wäre in
dem Augenblick veraltet, in dem der Dienst etwas dazubekommt, und genau so ist die Lücke
entstanden.*

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

> **Berichtigt 29.09.2026 — gemessen, und es kommt nicht an.** Die bestellte Messung
> (`auf-20260919-123`) kam am 21.09.2026 zurück: sieben Läufe am Vorgabe-Modell, einmal
> ohne und sechsmal mit Eingangsbild, verschiedene Bilder, verschiedene Stärken — **ein
> einziger Hashwert über alle sieben**, also Byte für Byte dasselbe Bild. Die Ursache lag in
> **unserem** Code: Ein Filter wirft Argumente hinaus, die die Pipeline nicht kennt, und
> `z-image-turbo` kennt `image` und `strength` nicht. Gerechnet wurde ein reines Textbild,
> und der Parametersatz sagte weiter `image_edit`. Seit dem 21.09.2026 sagt das Ergebnis es
> selbst (`modus_bestellt` gegen `modus_gerechnet`) — genau das stand am ersten echten Lauf
> vom 22.09.2026 (4.2) als erster Hinweis da.
>
> **Dieselbe Ursache trägt eine zweite Folge:** Auch die Sonne ändert das Endbild auf
> diesem Modell nicht (gemessen 22.09.2026 in `auf-20260922-137`, die Läufe aus
> `auf-20260921-127`: vier gerechnete Läufe mit drei Sonnenständen, bitgenau dasselbe
> Bild; am Code nachgewiesen in Sitzung 65). Eine
> Tiefenkarte trägt kein Licht, und der Weg, auf dem Licht ankäme — das Schönbild als
> Eingang —, ist derselbe, auf dem das Eingangsbild verschwindet.
>
> Die beiden neuen Knoten sind damit gebaut, geprüft und **auf dem Vorgabe-Modell
> wirkungslos**. Der Owner hat am 22.09.2026 entschieden, dass das Hineinskizzieren dort
> trotzdem rechnet — mit einem Hinweis am Bild. Welches Modell die Skizze tragen könnte, ist
> offen (Kapitel 6, 6.8).

**Viertens, nachgetragen am 29.09.2026: Der wichtigste Knoten hat nur noch eine Füllung.**
Seit `qwen-image-2512` stillgelegt ist, gibt es für den Knoten `render` mit
Tiefensteuerung genau ein freies Modell (4.2, Nachtrag). Die Kette ist an dieser Stelle so
austauschbar gebaut wie überall — es gibt nur nichts, womit man austauschen könnte.

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
| 4.6 Ihr Ergebnis (Nachtrag) | `auftraege/ergebnisse/auf-20260919-123.json`, `docs/sitzungen/2026-09-21_sitzung-41.md` |
| 4.2 Erster echter Lauf (Nachtrag) | `tools/beweis/31_der_weg_des_produkts.py`, `auftraege/ergebnisse/auf-20260922-137.json`, `docs/sitzungen/2026-09-22_sitzung-62.md` |
| 4.2 Render-Knoten (Nachtrag) | `backbone.VORGABE_BACKBONE`, `kosmo_szene` (Vorgabe ohne `vis.backbone`), `docs/EINBAU_STAND.md` C34–C36 und C38, `tests/test_ebenen_e124.py`, `docs/sitzungen/2026-09-29_sitzung-72.md` §4, §5, §9 |
| 4.3 Speicher in der Mappe (Nachtrag) | `docs/sitzungen/2026-09-21_sitzung-51.md` §3, `docs/sitzungen/2026-09-23_sitzung-70.md` §11 |
| 4.4 Bild über die Knotenansicht (Nachtrag) | `auftraege/ergebnisse/auf-20260924-164.json`, `docs/sitzungen/2026-09-24_sitzung-71.md` §7 und §12 |
