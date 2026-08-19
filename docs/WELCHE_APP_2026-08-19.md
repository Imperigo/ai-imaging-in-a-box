# Welche App wird eigentlich vorgeführt? — vier Bestände, und keiner ist sicher der richtige

**19.08.2026.** Zwei Berichte desselben Vormittags widersprachen sich, und beim Auflösen
kam etwas Grösseres heraus als der Widerspruch.

* `docs/COCKPIT_BESTAND_2026-08-19.md` fand eine **bedienbare Vis-Oberfläche** mit
  Treue-Regler, Auftragsliste und QA-Abzeichen — und ich habe darauf meine Empfehlung
  für Weg B gestützt.
* `docs/HOMESTATION-2026-08-19-DEMO-SIMULATION.md` bediente die laufende App als Mensch
  und fand **keinen Bereich KosmoVis** und einen Eintrag `Rendern`, der einen *Verlauf
  ohne Startknopf* öffnet.

Beide haben recht. Sie haben **verschiedene Programme** angesehen.

> ## BERICHTIGUNG, wenige Stunden später
>
> **Die HomeStation hat ihren eigenen Bericht korrigiert, und die zweite Fassung dreht
> den zweiten Spiegelstrich um.** Es gibt sehr wohl einen Bereich KosmoVis — er liegt
> eine Ebene tiefer, im Menü `Prepare · Vis · Publish`. Und es gibt einen **Knotengraph
> mit typisierten Anschlüssen**: zwölf Knoten in vier Gruppen, darunter ein
> **Render-Knoten mit den Eingängen `Szene`, `Prompt`, `Geometrie-Treue`, `Samples`,
> `Kamera-Standpunkte`** und ein **Auto-Kamera-Knoten** mit drei benannten Standpunkten.
> Dreimal war aus einem geschlossenen Menü auf Nichtvorhandensein geschlossen worden.
>
> **Was das an diesem Dokument ändert und was nicht.** Der Satz „die vorgeführte App hat
> keine Vis-Oberfläche" ist widerlegt — er stand hier und war falsch, und das gehört
> hierher und nicht in eine Fussnote. **Der Befund darunter steht unverändert:**
> `KosmoSpez` kommt in keinem Quelltext vor, den wir haben, und die Fassungsnummer passt
> zu keinem unserer Bestände. Wir wissen weiterhin nicht, welchen Code wir vor uns haben
> — nur, dass er mehr kann als gedacht.
>
> **Und die Lage ist damit deutlich besser, als sie gestern aussah:** Der Regler, um den
> sich diese Vertiefungsarbeit dreht, heisst dort schon `Geometrie-Treue` und ist ein
> Anschluss am Render-Knoten. Die Kameras, die der Demoplan für den grössten Mangel
> hielt, gibt es als Knoten.
>
> **Der eine Befund, der uns unmittelbar angeht:** Der Knopf «Ausführen» meldet
> *«bereit»* und tut nichts — kein Fortschritt, kein Fehler, keine Begründung. Die
> wahrscheinliche Ursache ist, dass die Knoten gesetzt, aber **nicht verdrahtet** sind.
> **Das ist wörtlich der Befund, mit dem dieses Projekt angefangen hat**, nur an anderer
> Stelle: *ein Zustand, der Bereitschaft behauptet, ohne sie zu prüfen.* Unser
> `kette.pruefe_kette` und `graph.pruefe_bedarf` beantworten genau diese Frage vor dem
> Lauf — das ist die Stelle, an der unsere Arbeit dort etwas beitragen könnte, und zwar
> unabhängig davon, welcher Weg gewählt wird.

---

## Die vier Bestände

| # | Bestand | Was drin ist | Belegt durch |
|---|---|---|---|
| 1 | `Imperigo/kosmoorbit`, Commit `a69af5d` | **Der Knoten-Cockpit.** `src/lib/pipeline.ts` mit `nodeReadinessIssues`, `FIELD_ALIAS_GROUPS`, `mergeInputs`; `NodePipeline.tsx`. **Darauf ist unsere ganze MCP-Schicht ausgelegt** (Phase 0). | Dateien vorhanden, `git remote` und Commit geprüft |
| 2 | `Architektur-Cosmos/kosmo-orbit`, Fassung `1.0.0-v1` | **Die Designzentrale V1.** Fünf Kacheln, darunter `vis` → `VisWorkspace.tsx` mit Treue-Regler und QA-Abzeichen. Die Kachel ist **nicht** ausgeblendet: `modules` wird ungefiltert gezeichnet, `onClick` setzt den Bildschirm. | `App.tsx` Zeile 49 und 337 gelesen |
| 3 | **Die App, die vorgeführt wurde** — „KosmoOrbit v0.9.35" auf :5183 | Vier Stationen: **KosmoData, KosmoDesign, KosmoSpez, KosmoOffice**. 81 Werkzeuge in Inseln. `Rendern` ist ein Verlauf ohne Startpunkt. | Demo-Simulation, am Bildschirm bedient |
| 4 | `Imperigo/kosmovis`, `Imperigo/kosmodraw` | Die Nachbar-Lanes. | vorhanden |

---

## Der Befund, der zählt

**`KosmoSpez` kommt in keinem einzigen Quelltext vor, den wir haben.**

```
grep -rln "KosmoSpez"  über alle Klone und /workspace  →  nichts
grep -rln "KosmoOffice"                                →  zwei PLANUNGSDOKUMENTE, kein Code
```

Die Demo-Simulation nimmt an, auf :5183 laufe `Architektur-Cosmos/kosmo-orbit`. **Das
kann nicht sein:** Jener Bestand hat fünf Kacheln statt vier Stationen, kennt weder
`KosmoSpez` noch `KosmoOffice`, keine Werkzeug-Inseln und keine 81 Werkzeuge — und er
trägt die Fassung `1.0.0-v1`, nicht `0.9.35`.

> **Die App, die vorgeführt werden soll, liegt uns nicht vor.**

Das ist keine Nachlässigkeit der Simulation — sie hat die App richtig beschrieben und
nur den Bestand danebengegriffen. Aufgefallen ist es erst beim Auflösen des Widerspruchs
zwischen zwei Berichten. *Zwei Berichte, die sich widersprechen, sind wertvoller als
einer, dem man glaubt.*

---

## Was das für die beiden Wege heisst

**Beide Wege zielen auf Programme, die nicht das vorgeführte sind.**

* **Weg A** (MCP-Knoten) zielt auf Bestand 1. Dort liegt der Knotengraph, dort greift
  `pipelineReadiness`, dorthin passt unsere MCP-Schicht. In der vorgeführten App gibt es
  keinen Knotengraph.
* **Weg B** (HTTP-Brücke) zielt auf Bestand 2. Dort liegt die Vis-Oberfläche mit den
  QA-Abzeichen. In der vorgeführten App gibt es keinen Bereich KosmoVis.

**Meine Empfehlung von heute früh — „Weg B, weil es dort schon eine bedienbare
Oberfläche gibt" — steht damit auf einer Voraussetzung, die ich nicht geprüft hatte:**
dass jene Oberfläche in der App steckt, die am Semesterende auf der Leinwand ist.

Die Arbeit an der Naht ist deswegen nicht verloren: `kosmo_szene.py` und `bruecke.py`
übersetzen **Verträge**, nicht Oberflächen, und die Verträge sind in allen drei Beständen
dieselben (`kosmovis.render-scene/v1`, `render-result/v2`). Aber welcher Weg *zur Demo*
führt, ist offen — und zwar aus einem Grund, der vorher nicht auf der Liste stand.

---

## Was jetzt zu klären ist, bevor jemand weiterbaut

`auf-20260819-16` fragt die HomeStation nach drei Zeilen: Welches Verzeichnis wird auf
:5183 bedient, was steht in dessen `package.json`, und was sagen `git remote -v` und
`git log -1`. Das ist in zwei Minuten beantwortet und entscheidet, wohin die nächsten
Tage Arbeit gehen.

**Bis dahin baue ich nichts, was an einer bestimmten Oberfläche hängt.** Was
weitergebaut werden kann, ohne diese Antwort: alles an den Verträgen, an der QA und an
der Bildkette — das trägt in jedem der drei Fälle.
