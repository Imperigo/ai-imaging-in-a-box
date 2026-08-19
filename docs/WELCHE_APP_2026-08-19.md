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

> ## ZWEITE BERICHTIGUNG — vom Owner, und sie ordnet das Ganze
>
> **„Das, was wir hier machen, ist KosmoVis innerhalb von KosmoDesign. Hat nichts mit
> KosmoSpez zu tun."**
>
> Damit fällt die Beweisführung unten in sich zusammen, und zwar zu Recht. `KosmoSpez`
> ist eine **eigene Lane** — Sonnenstudie, Klimasteckbrief, Tageslicht, Thermik, Wind,
> Statik. Dass sie in unseren Klonen fehlt, ist **kein Rätsel, sondern richtig**: Wir
> haben die Lanes geklont, die uns angehen, und diese gehört nicht dazu.
>
> Ich habe aus der Abwesenheit einer fremden Lane auf die Unbekanntheit der ganzen App
> geschlossen. Das ist derselbe Fehlschluss, den die HomeStation im selben Bericht an
> sich selbst protokolliert hat — *aus einem geschlossenen Menü auf Nichtvorhandensein
> schliessen* —, nur eine Ebene höher: **aus einer nicht geklonten Lane auf einen
> unbekannten Bestand.**
>
> **Was übrig bleibt, und es ist kleiner und schärfer:** Die vorgeführte App ist eine
> **Schale**, die mehrere Lanes als Stationen zeigt. Wir haben die Lanes, nicht die
> Schale. Die einzige Frage, die uns wirklich angeht, lautet damit nicht „welche App",
> sondern:
>
> > **Wo liegt der Quelltext von `Design/Vis` — der Knotenoberfläche mit dem
> > Render-Knoten?**
>
> Das sind die vierzehn Werkzeuge `palette, ausrichten, verbinden, zoom, raster, routing,
> ansichten, legende, stimmung, render-senden, aufs-plakat, kamera-vorschlagen, report,
> sonnenstunden`. Dort sitzt der Eingang `Geometrie-Treue`, dort schweigt der Knopf
> «Ausführen», und dort gehört unsere Lane hin.
>
> Die vier Bestände unten bleiben als Bestandsaufnahme richtig. Nur die Folgerung war zu
> breit.

---

## Der Befund, der zählt — und wie weit er trägt

**`KosmoSpez` kommt in keinem einzigen Quelltext vor, den wir haben.** *(Siehe die
Berichtigung oben: Das ist erwartbar, weil es eine fremde Lane ist. Der Abschnitt bleibt
stehen, weil er zeigt, wie die Frage entstanden ist — und woran ich zu weit geschlossen
habe.)*

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

**Nach der Berichtigung des Owners ist die Frage schärfer und kleiner:** Nicht „welche
App", sondern **wo `Design/Vis` liegt** — der Bereich mit dem Knotengraph, dem
Render-Knoten und dem Eingang `Geometrie-Treue`. Alles andere an jener Schale geht uns
nichts an.

---

## DRITTE BERICHTIGUNG — und sie erklärt vermutlich alles

**Der Owner: „Beachte auch, dass der Cloud-Worker an der KosmoOrbit-Software ebenfalls
baut, in anderen Bereichen."**

Damit löst sich das Rätsel wahrscheinlich ohne weitere Suche auf. Nachgesehen:

```
grep -rn "render-senden|kamera-vorschlagen|Design/Vis"  über alle Bestände  →  nichts
```

Die vierzehn Werkzeuge von `Design/Vis` liegen in **keinem** Quelltext, den wir haben.
Die naheliegendste Erklärung ist nicht mehr „ein unbekannter Bestand", sondern:

> **Diese Oberfläche wird gerade gebaut — nach dem Stand unserer Klone.**

Ein Auto-Kamera-Knoten mit drei benannten Standpunkten und ein Render-Knoten mit dem
Eingang `Geometrie-Treue` sind kein Zufallsfund in altem Code. Das ist frische Arbeit an
genau der Stelle, an der auch wir stehen.

### Was daraus folgt — und es ist eine Kehrtwende

**Einen bewegten Bestand rückwärts zu lesen ist verschwendete Arbeit.** Jede
Bestandsaufnahme ist am Tag ihrer Fertigstellung überholt, und je genauer wir eine
fremde Oberfläche nachbauen, desto sicherer bauen wir am selben Tag daneben.

Und es besteht eine reale Gefahr der **Doppelarbeit**: Wenn dort eine Vis-Oberfläche
entsteht und wir hier eine Brücke zu einer *anderen* Oberfläche bauen, hat am Ende
niemand etwas davon.

**Die wirtschaftliche Antwort ist nicht Nachbauen, sondern Zusagen.** Was unsere Lane
braucht und liefert, steht in Verträgen, nicht in Bildschirmen — und Verträge halten,
während eine Oberfläche sich ändert. Darum entsteht statt weiterer Bestandsaufnahmen ein
**Übergabeblatt**: `docs/UEBERGABE_VIS_2026-08-19.md`, geschrieben für den, der die
Vis-Oberfläche baut.

Es beantwortet drei Fragen und sonst nichts: *Was schicke ich euch? Was bekomme ich
zurück? Und woran erkenne ich, dass eine Verbindung wirklich trägt?* Die letzte ist die
wichtigste — sie ist die Antwort auf den Knopf, der `bereit` meldet und schweigt.

**Bis dahin baue ich nichts, was an einer bestimmten Oberfläche hängt.** Was
weitergebaut werden kann, ohne diese Antwort: alles an den Verträgen, an der QA und an
der Bildkette — das trägt in jedem der drei Fälle.


---

# VIERTE BERICHTIGUNG — die Prämisse dieses Dokuments trug nicht

**`auf-20260819-16` ist beantwortet (20.08.2026). Die drei Zeilen:**

| Frage | Antwort |
|---|---|
| Welches Verzeichnis? | `apps/kosmo-orbit` — genau der Bestand, den der Bericht genannt hatte |
| `package.json`? | `@kosmo/orbit-app`, **0.9.36** (die Oberfläche zeigt 0.9.35, weil der laufende Build älter ist als die Versionszeile) |
| `git remote` / `git log`? | **`Imperigo/Architektur-Cosmos` — das eigene Repo des Owners.** Letzter Commit **am selben Tag, 10:00:56**, null uncommittete Änderungen |

**Und damit fällt die Prämisse, auf der dieses Dokument aufgebaut ist.**

Der Anlass war der Satz: *„`KosmoSpez` kommt in keinem Quelltext vor, den wir haben."*
Er stimmte — aber er belegte nicht, was ich daraus gemacht habe. Dort steht `KosmoSpez`
in **31 Dateien**. **Unser Klon ist schlicht älter als der Arbeitsstand.**

Es war nie ein unbekannter Bestand. Es war unser eigener, veralteter Blick darauf.

## Warum das trotzdem kein verlorener Tag war

Die dritte Berichtigung — die des Owners, dass der Cloud-Worker gerade an KosmoOrbit
baut — war **richtig und ist jetzt belegt**: Der letzte Commit ist von heute Vormittag,
`VisWorkspace.tsx` liegt dort, `NodePipeline` und `pipelineReadiness` noch nicht. Die
Vis-Oberfläche entsteht in diesem Moment.

Und die Kehrtwende, die daraus folgte, wird durch diesen Befund **bestätigt statt
widerlegt**:

> Einen bewegten Bestand rückwärts zu lesen ist verschwendete Arbeit.

Ein Bestand, dessen letzter Commit vom selben Vormittag ist, war beim Beginn meiner
Bestandsaufnahme schon nicht mehr der, den ich beschrieb. Das Übergabeblatt
(`docs/UEBERGABE_VIS_2026-08-19.md`) ist die richtige Antwort darauf, und es bleibt
gültig — es beschreibt Verträge und keine Bildschirme.

## Der Merksatz, um einen Halbsatz erweitert

Bisher hiess er:

> Die Existenz einer Datei ist kein Beleg für ihren Inhalt — und ihr Fehlen keiner für
> ihre Abwesenheit.

Der zweite Halbsatz stimmte und war zu eng gefasst. **Ihr Fehlen in einem Klon ist nicht
einmal ein Beleg für ihr Fehlen im Bestand.** Ich habe eine Momentaufnahme mit dem
Gegenstand verwechselt — dreimal an einem Tag, in drei Verkleidungen: das geschlossene
Menü, das fehlende `KosmoSpez`, das nirgends auffindbare `Design/Vis`.

## Und ein Befund der HomeStation über sich selbst, der hierher gehört

Sie hat im selben Bericht einen eigenen Fehler gemeldet: Sie hatte den vierten Wächter
als *grün* gemeldet, er habe eine Auflösung von 1024×768 geprüft. Das Fundartefakt aus
ihrem eigenen Lauf trägt `{"geprueft": 0}`. **Er hat nichts gemessen.**

Sie hatte aus *„Test bestanden"* auf *„Wächter hat geprüft"* geschlossen, ohne
nachzusehen. Das ist derselbe Fehler in einer weiteren Verkleidung, und er verdient einen
eigenen Satz:

> **Ein bestandener Test ist kein Beleg dafür, dass er etwas geprüft hat.**

Genau dagegen steht in diesem Projekt die Dreiteilung *bestanden / durchgefallen /
**nicht gemessen***, inzwischen an fünf Stellen — und die Regel, dass eine ungemessene
Schwelle nicht verurteilen darf.


---

# FÜNFTE BERICHTIGUNG — der Klick ging daneben

**20.08.2026.** Die HomeStation hat einen weiteren eigenen Befund gemeldet, und er trifft
einen Satz, den ich dreimal weitergegeben habe.

Notiert war: *„Ausführen dreimal gedrückt — keine Zustandsänderung."* Daraus geschlossen:
Der Zustand melde `bereit`, ohne die Verdrahtung zu prüfen.

Nachgemessen mit `document.elementFromPoint` an genau der Klickkoordinate:

```
911,759  →  island-render-senden-popup-vergroessern
```

Der **Vergrössern-Knopf** (44 × 44 bei 895,741) überdeckt die obere linke Ecke des
**Ausführen-Knopfs** (84 × 32 bei 911,759). Der Klickpunkt lag darin. Unabhängig
bestätigt: Ihr eigener Insel-Überdeckungs-Wächter hat dieselbe Stelle gefunden — Station
`vis`, Zustand `popup:render-senden`, bei 1400 × 900, also genau jener Fenstergrösse.

**Was steht:** Das Panel *zeigte* `bereit` bei unverdrahteten Knoten. Das ist eine
**Ablesung** und kein Klick, und es bleibt der Befund, um den es geht.

**Was nicht mehr gilt:** dass ein Druck im unverdrahteten Zustand wirkungslos bleibt. Der
Druck ist nie ausgelöst worden. Ob `bereit` dort lügt, ist **ungemessen**.

## Und es ist derselbe Fehler wie an vier anderen Stellen dieses Tages

> **Aus einem ausbleibenden Effekt auf eine Ursache geschlossen, ohne zu prüfen, ob die
> Handlung überhaupt ankam.**

Die Reihe wird lang, und sie hat immer dieselbe Form — ein Schluss aus einer Abwesenheit,
ohne die Voraussetzung zu prüfen:

| Abwesenheit | Falscher Schluss | Was wirklich war |
|---|---|---|
| geschlossenes Menü | „gibt es nicht" | war nur nicht aufgeklappt |
| `KosmoSpez` fehlt im Klon | „fremder Bestand" | Klon veraltet |
| `Design/Vis` nirgends auffindbar | „andere App" | wird gerade gebaut |
| Wächter grün | „hat geprüft" | `{"geprueft": 0}` |
| kein Effekt beim Klick | „Knopf tut nichts" | Klick kam nie an |

Fünf Verkleidungen, ein Fehler. Er verdient den Satz, der ihn abkürzt:

> **Bevor du aus einem Ausbleiben etwas schliesst, prüfe, ob die Ursache überhaupt
> gewirkt haben konnte.**
