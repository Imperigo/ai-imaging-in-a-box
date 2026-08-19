# Demo-Simulation: was am 19.08.2026 wirklich geht

**Home-PC-Worker, als menschlicher Nutzer.** Maus und Tastatur über CDP im echten
Chromium, keine API-Abkürzungen — sonst prüfte ich das Backend statt der Bedienbarkeit.
Grundlage: `docs/DEMOPLAN_2026-08-18.md`, acht Schritte. App: **KosmoOrbit v0.9.35** auf
:5183, frisches Profil. 10 Screenshots, ausserhalb der Repos.

---

## Die Antwort in drei Sätzen

**Der Entwurfsteil ist weiter, als der Demoplan vermuten lässt** — 81 Werkzeuge über drei
Stationen, ein Beispielprojekt mit echtem Grundriss, und eine Einrichtung, die live misst
statt zu behaupten.

**Der Bildteil existiert als Oberfläche nicht.** Es gibt genau einen Eintrag `Rendern`, und
der öffnet einen Verlauf ohne Startknopf.

**Und Schritt 3 des Skripts hat keinen Einstieg:** einen Bereich «KosmoVis» gibt es nicht.

---

## 1 · Die acht Schritte, gemessen

| # | Vision | Stand | Belegt durch |
|---|---|---|---|
| 1 | Modell laden | **GEHT** | «Beispielprojekt TKB Bibliothek Hönggerberg» lädt in ~5 s |
| 2 | Übersetzen (Ebenen, Klassen, **Materialien**) | **TEIL** | Räume, Beschriftung, Möblierung, Masskette 28.25 m sichtbar; `materialien` existiert in KosmoData, Durchgriff ungeprüft |
| 3 | KosmoVis öffnen | **FEHLT** | Stationen: Data · Design · Spez · Office (kommend). Kein KosmoVis |
| 4 | Preset-Dialog (Kameras, HDRI, Stimmung, Stil) | **FEHLT** | kein Werkzeug dieser Art unter 81 |
| 5 | Node-Oberfläche | **FEHLT hier** | `graph` ist der Raumgraph; die Knoten-Pipeline liegt in einem **anderen Codebestand** |
| 6 | Knoten (Prompter, Kamera, Stil, Render, Kompositor) | **FEHLT** | siehe 4 und 5 |
| 7 | Output (n Bilder, Varianten, Zonen) | **TEIL** | `varianten` sind Entwurfs-, keine Bildvarianten |
| 8 | Vorschau + an Publisher | **TEIL** | `export`, `blaetter` da; Weiterreichen ungeprüft |

## 2 · Was überraschend gut geht

**Die Einrichtung misst.** Vier Schritte, und in Schritt 2 prüft sie die Bridge auf :8600
**live** — «Zentrale gefunden», Version 1.0.0, Dienste `jobstore, ollama`. Schritt 3 meldet
«3 von 3 Kern-Werkzeugen laufen» und nennt Ollama, `qwen3:30b` und die Bridge einzeln. Alle
Zustände stimmten mit dem überein, was ich vorher hochgefahren hatte. Der Satz im Dialog —
*«kein erfundener Ladebalken»* — hält der Prüfung stand.

**Das Beispielprojekt trägt eine Demo.** Vier Wohnungen mit Nasszellen und Küchen,
Erschliessung, Möblierung, Beschriftung, durchgehende Masskette über 28.25 m, dazu
Geschossplatten in 3D. Für Schritt 1 und 2 braucht es keine ArchiCAD-Datei.

**Der Werkzeugbestand, vollständig erhoben (81):**

- **KosmoDesign · Zeichnen (24):** auswahl, wand, oeffnung, volumen, zone, dach, treppe,
  stuetze, skizze, mesh, messen, gelaender, rampe, detail, hoehenkote, winkelmass,
  radialmass, notiz, linienzug, kreis, schraffurflaeche, unterzug, decke, schnitt
- **· Ansicht (6):** darstellung, sonne, ebenen, achsen, trace, graph
- **· Projekt (6):** kennzahlen, checks, varianten, liste, kommentare, profil
- **· Austausch (6):** export, import, **rendern**, blaetter, sync, manuell
- **KosmoSpez (20):** sonnenstudie, klimasteckbrief, aussenkomfort, tageslicht, thermik,
  wind, statik, overlay-wahl, falschfarben-skala, zeitregler, vergleich-ab, ergebnisliste,
  annahmen-datenquellen, grenzen, kennwerte, export, klimadaten-import, homestation,
  kontext-scan, manuell
- **KosmoData (15):** referenzen-suche, uebersicht, referenzen, bauteile, materialien,
  archiv, wissen, training, gedaechtnis, dev, kennzahlen, sync, import, vollbild, manuell

## 3 · Die zwei Befunde, die die Demo betreffen

### Es gibt keinen Bereich «KosmoVis»

Der Stationen-Orb führt vier: **KosmoData, KosmoDesign, KosmoSpez, KosmoOffice** (letzteres
als «kommend» markiert). Das ist kein Fehler, sondern die Folge des Namens-Kanons vom
12.08. (Design ⊃ Prepare/Vis/Publish). **Das Demoskript kennt diese Faltung nicht** — es
sagt «KosmoVis öffnen, Visualisierungsprojekt erstellen», und beides hat keinen Einstieg.

Wer Schritt 3 vorführen will, hat zwei Wege: das Skript umschreiben (Vis als Bereich
*innerhalb* von Design) oder den Bereich bauen. Das ist eine Entscheidung, keine Aufgabe.

### Der Render lässt sich nicht starten

`Rendern` gibt es, in der Austausch-Insel von KosmoDesign. Angeklickt öffnet es ein Panel
mit genau einem Satz:

> Kein Render-Lauf in dieser Sitzung

Auf Bedienelemente abgesucht: **keine** ausser Vergrössern und Schliessen. Es ist ein
**Verlauf ohne Startpunkt**. Damit haben die Schritte 4 bis 7 keinen Weg durch die
Oberfläche — nicht weil sie schlecht wären, sondern weil es sie nicht gibt.

## 4 · Zwei Irrwege von mir, protokolliert

**Erstens:** Meine erste Suche nach Vis-/Render-Einträgen meldete «keine Treffer». Sie lief,
**bevor** die Inseln geöffnet waren, und die Werkzeuge entstehen erst beim Aufklappen. Die
Suche war richtig, der Zeitpunkt falsch. Nach dem Öffnen: 46 Werkzeuge allein in Design.
Hätte ich nicht nachgesehen, stünde hier ein falscher Befund.

**Zweitens:** Ich hielt die parallel laufende E2E-Suite für hängengeblieben — 0 % CPU beim
Elternprozess, letztes Artefakt 45 Minuten alt. Beides stimmte und beides bewies nichts:
Der Elternprozess wartet naturgemäss, und nicht jeder Test schreibt ein Artefakt. Ein
frischer Chromium war 30 Sekunden alt und rechnete. Aus zwei schwachen Zeichen zu schnell
geschlossen.

## 5 · Ein Nebenbefund mit Folgen

Die Knoten-Pipeline aus Schritt 5 liegt **nicht in der laufenden App**. `NodePipeline.tsx`
und `pipelineReadiness` stehen in einem zweiten KosmoOrbit-Codebestand unter
`/mnt/data/.../Code/KosmoOrbit/`; auf :5183 läuft `Architektur-Cosmos/kosmo-orbit`.

Das betrifft den gestrigen Backend-Fix: Dass die MCP-Schemata jetzt durchgereicht werden
und `pipelineReadiness` erstmals urteilen kann, gilt für eine App, die hier **nicht** läuft.
Wer die Knoten-Oberfläche in der Demo zeigen will, zeigt einen anderen Codebestand.

## 6 · Was ungemessen blieb

- **Materialien** (Schritt 2): `materialien` existiert in KosmoData, ob es am geladenen
  Modell hängt, ist nicht geprüft.
- **Sonnenstudie** (KosmoSpez): 20 Werkzeuge vorhanden, keines ausgeführt.
- **Export und Blätter** (Schritt 8): vorhanden, nicht durchlaufen.
- **Kosmo selbst**: der Orb ist da, kein Gespräch geführt.

Das ist kein Versäumnis, sondern die Grenze eines Vormittags — und es steht hier, damit
niemand den Bericht für vollständiger hält, als er ist.
