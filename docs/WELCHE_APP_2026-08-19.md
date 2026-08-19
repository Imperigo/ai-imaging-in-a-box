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
