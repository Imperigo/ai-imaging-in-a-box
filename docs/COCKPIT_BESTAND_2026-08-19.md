# Wo die Oberfläche der Demo-Vision technisch lebt

**19.08.2026 · Bestandsaufnahme am Quelltext, nichts davon aus zweiter Hand**

Diese Datei beantwortet vier Fragen: Wo liegt das Cockpit? Wie werden Werkzeuge dort
registriert und aufgerufen? Gibt es schon eine Knotenoberfläche? Und was braucht unsere
Lane, um in der Demo aufzutauchen?

Sie ist für jemanden geschrieben, der nicht programmiert. Fachbegriffe werden bei der
ersten Verwendung erklärt; was im `docs/LEXIKON.md` fehlt, steht am Ende gesammelt.

---

## 0 · Die Kurzfassung in fünf Sätzen

1. **Das Cockpit existiert und ist vollständig lesbar** — aber nicht dort, wo gesucht
   wurde. Es liegt im Repo `Imperigo/KosmoOrbit`, in dieser Sitzung ausgecheckt unter
   `/workspace/kosmoorbit`, Stand `a69af5d` — genau der Stand, den `docs/EINBINDUNG_KOSMOORBIT_2026-08-14.md`
   zitiert. Die Datei `src/lib/pipeline.ts` mit `nodeReadinessIssues` und
   `FIELD_ALIAS_GROUPS` ist da, ebenso `src/components/NodePipeline.tsx` (1 700 Zeilen
   Knotenoberfläche).
2. **Es gibt zwei verschiedene Dinge namens „KosmoOrbit"**, und sie zu verwechseln ist
   die eigentliche Falle dieser Sitzung — mehr dazu in Kapitel 1.
3. **Alle drei Befunde des HomeStation-Berichts vom 18.08. stimmen und stehen wörtlich
   im Quelltext.** Zwei davon sind nicht konfigurierbar (Server-Kennung im Werkzeugnamen,
   `_BUILTIN_SERVERS`), einer ist eine Betriebseigenheit ohne Schalter (Neustart nach
   Registrierung).
4. **Die Knotenoberfläche gibt es — aber sie ist ein anderes Werkzeug als das der
   Demo-Vision.** Sie verdrahtet MCP-Werkzeuge, nicht Bildparameter. Kein einziger der
   in der Vision genannten Knoten (Prompter, 3D-Kamera, Bildstil, Kompositor,
   Material-/Farbebene, „start imaging") existiert dort.
5. **Unsere Lane hat heute keinen Weg auf die Leinwand**, weil das Cockpit für
   Dritt-Server keine Schemata durchreicht und alle unsere Werkzeuge hinter der
   Admin-Sperre liegen. Beide Hebel liegen in **fremden** Repos.

---

## 1 · Wo ist das Cockpit? — Die Antwort und die Falle

### 1.1 Es gibt zwei „KosmoOrbit"

Das ist der wichtigste Befund dieser Sitzung, weil er jede frühere und jede künftige
Suche in die Irre führt, solange er nicht aufgeschrieben ist.

| | **KosmoOrbit (Cockpit)** | **KosmoOrbit V1 (Designzentrale)** |
|---|---|---|
| Repo | `Imperigo/KosmoOrbit` (eigenes Repo) | Unterordner `kosmo-orbit/` **im Website-Repo** `Imperigo/architektur-cosmos` |
| Hier zu finden | `/workspace/kosmoorbit` (632 Dateien) | `…/scratchpad/oekosystem/Architektur-Cosmos/kosmo-orbit/` (131 Dateien) |
| Stand | `a69af5d`, gelesen am 14.08. | `79a7ca7`, Roadmap-Stand 02.07.2026 |
| Bauart | Tauri + React + Vite, spricht mit dem **Odysseus-Backend** auf `127.0.0.1:7860` | Tauri + React + Vite, eigener Kern (`packages/kosmo-kernel`), spricht mit einer **eigenen HomeStation-Bridge** auf Port 8600 |
| Knotenoberfläche | **ja** (`NodePipeline.tsx`, xyflow) | **nein** — fünf feste Module Design/Data/Vis/Publish/Prepare |
| Unser Anknüpfungspunkt | MCP-Werkzeuge | HTTP-Auftrag mit `render-scene`-Datei |

*Erklärung für Nicht-Programmierer:* Ein **Repo** ist ein Projektordner mit
Versionsgeschichte. Zwei Projekte dürfen denselben Namen tragen — hier tun sie es, und
sie sind technisch fast nichts miteinander gemein. „Tauri", „React", „Vite" sind
Baukästen für Oberflächen; „xyflow" ist ein Baukasten speziell für Knoten-Diagramme, die
man mit der Maus verdrahtet.

**Konsequenz:** Wer „KosmoOrbit" sagt, muss künftig dazusagen, welches. Ich schlage vor:
**Cockpit** für das erste, **Designzentrale** für das zweite.

### 1.2 Warum die Suche im Ökosystem-Ordner leer ausging

Die sieben Klone unter `…/scratchpad/oekosystem/` enthalten das Cockpit **nicht**. Die
Suche nach `FIELD_ALIAS_GROUPS`, `nodeReadinessIssues`, `pipelineReadiness` und
`mergeInputs` dort findet ausschliesslich **Dokumentation über** den Code, nie den Code:

- `ArchitekturKosmos-Codex/_overseer/PIPELINE-FELD-ALIASE-2026-06-16.md` — beschreibt die
  Alias-Tabelle vollständig und nennt sie ausdrücklich „implementiert, `src/lib/pipeline.ts`"
- `ArchitekturKosmos-Codex/_overseer/MCP-V1-TOOL-VERTRAEGE-2026-06-16.md`
- `KosmoDesign/docs/CROSS_WORKER_INFO_2026-06-23_…-cockpit-seam-…md`

Das ist ein Muster, das man kennen sollte: Im `_overseer`-Ordner des Codex-Repos liegen
**Berichte und Sicherungskopien über fremde Codebasen**, nicht die Codebasen selbst.

### 1.3 Die Vollständigkeitsprüfung — kein Klon war unvollständig

Der Auftrag warnte vor einem unvollständig ausgecheckten Klon (5 Dateien im
Arbeitsbaum, 314 in der Versionsgeschichte). **Ich habe alle neun erreichbaren Klone
geprüft und keinen unvollständigen gefunden — ein `git reset --hard` war nirgends nötig
und wurde nirgends ausgeführt.**

| Klon | Dateien im Arbeitsbaum | Dateien in der Versionsgeschichte | Zustand |
|---|---:|---:|---|
| `Architektur-Cosmos` | 5114 | 5114 | sauber |
| `ArchitekturKosmos-Codex` | 559 | 562 | sauber¹ |
| `KosmoDesign` | 433 | 433 | sauber |
| `KosmoPrepare` | 391 | 391 | sauber |
| `KosmoPublish` | 519 | 519 | sauber |
| `KosmoVis` (scratchpad) | 314 | 314 | sauber — **war offenbar der Problemfall und ist bereits repariert** |
| `architekturkosmos-control-hub` | 246 | 246 | sauber |
| `/workspace/kosmoorbit` | 632 | 632 | sauber |
| `/workspace/kosmovis`, `/workspace/kosmodraw` | 314 / 639 | 314 / 639 | sauber |

¹ Die drei Differenzen sind zwei Untermodul-Verweise und ein Bau-Verzeichnis, keine
fehlenden Dateien. `git status` meldet in **allen** Klonen einen sauberen Arbeitsbaum.

**Was das heisst:** Der Vorgänger, der auf 5 Dateien stiess, hat den Zustand offenbar
schon behoben. Die Warnung bleibt trotzdem richtig und gehört ins Vorgehen.

---

## 2 · Wie MCP-Server registriert werden und Werkzeuge aufgerufen werden

*Erklärung:* **MCP** ist ein Protokoll, über das ein Programm einem Sprachmodell oder
einem Cockpit seine „Werkzeuge" anbietet — benannte Funktionen mit einem Formular für
die Eingaben (`inputSchema`) und einer Zusage über die Ausgaben (`outputSchema`). Unser
Repo bietet drei solche Werkzeuge an: `aiimaging_enqueue_render` (Auftrag anlegen),
`aiimaging_query_render` (Status lesen), `aiimaging_check_geometry` (Geometrie prüfen).

Der Quelltext des Backends liegt **nicht** in einem der Kosmo-Repos. Er ist ein fremdes
Produkt namens **Odysseus** (`github.com/pewdiepie-archdaemon/odysseus`), das nach
`vendor/odysseus/` gespiegelt und dort ergänzt wird — der Ordner ist bewusst aus der
Versionsverwaltung ausgenommen. Was greifbar ist, sind **Sicherungskopien der geänderten
Dateien** unter
`…/oekosystem/ArchitekturKosmos-Codex/_overseer/backend-pipeline-endpoints/`
(`pipeline_routes.py`, `mcp_routes.py`, `mcp_manager.py.partial`). An diesen Kopien habe
ich geprüft.

### 2.1 Befund «der qualifizierte Name trägt die Kennung, nicht den Namen» — **stimmt, nicht konfigurierbar**

`mcp_manager.py.partial`, Zeile 515 und 539:

```python
qualified = f"mcp__{server_id}__{tool['name']}"
```

`server_id` ist die vom Backend vergebene Kennung (bei uns `d99fcf67`), nicht der Name
`aiimaging`. Es gibt an dieser Stelle **keinen Schalter und keine Alternative** — der
Name wird an zwei Stellen identisch zusammengesetzt und in `mcp_routes.py` beim Aufruf
wieder in drei Teile zerlegt.

**Folge für uns:** Ein Werkzeugaufruf muss immer die aktuelle Kennung tragen. Sie ändert
sich, wenn der Server neu registriert wird. Das Cockpit löst das richtig: Es sucht
Werkzeuge über den **schlichten** Namen und liest die Kennung aus der Werkzeugliste
(`recipes.ts` → `tlist.find(t => t.name === s.tool)?.qualifiedName`). **Wer eine
Kennung fest in ein Rezept oder eine Anleitung schreibt, baut eine Zeitbombe.**

### 2.2 Befund «ein zur Laufzeit registrierter Server braucht einen Neustart» — **plausibel, aber am Quelltext nicht abschliessend belegbar**

Der Bericht misst es sauber: `connected: true`, drei Werkzeuge sichtbar, und der Aufruf
scheitert neun Millisekunden später mit `Connection closed`. Die Protokollzeile
*„Attempted to exit cancel scope in a different task than it was entered in"* passt zum
Bild: Die Verbindung hängt an der Aufgabe, die die Registrierungsanfrage bearbeitet hat,
und stirbt mit ihr.

Im Quelltext ist die **Stelle** sichtbar, an der das entstehen kann — `_connect_stdio`
legt die Verbindung in einem `AsyncExitStack` an und hebt sie in
`self._sessions[server_id]` auf, also über das Ende der Anfrage hinaus. Ob genau diese
Fassung auf der HomeStation läuft, **kann ich hier nicht feststellen** (siehe Kapitel 6).

**Konfigurierbar: nein.** Es gibt keinen Schalter „Server nach Registrierung neu
aufbauen". Der Neustart des Backends ist der Weg. **Merkregel bleibt:** Nach jeder
Registrierung `systemctl --user restart kosmo-backend`, und `connected: true` ist kein
Beleg.

### 2.3 Befund «alles hinter `require_admin`, weil nur vier Server als lesend gelten» — **stimmt wörtlich, und es ist eine Datei-Konstante**

`pipeline_routes.py`, Zeilen 126 und 144:

```python
_BUILTIN_SERVERS = {"image_gen", "memory", "rag", "email"}
...
    if server_id not in _BUILTIN_SERVERS:
        return False        # → gilt als mutierend → require_admin
```

Der Ablauf, den `is_read_only_tool` nimmt, in Worten:

1. Name in drei Teile zerlegen; passt die Form nicht → **gesperrt**.
2. Steht der schlichte Werkzeugname in der Liste `READ_ONLY_MCP_TOOLS` → **frei**.
3. Sonst: Ist der Server einer der vier eingebauten → Verb-Heuristik (`query_…`,
   `list_…`, `get_…` gelten als lesend).
4. Sonst → **gesperrt**.

Unsere Werkzeuge fallen in Schritt 4. `aiimaging_query_render` beginnt zwar mit `query`,
aber die Heuristik wird für Dritt-Server gar nicht erst erreicht. Die Allowlist führt
`kosmodesign_*`, `kosmoprepare_*`, `kosmovis_*`, `kosmodraw_*`, `kosmopublish_*`,
`kosmodev_*` — **`aiimaging_*` fehlt.** Genau wie der Bericht sagt.

**Konfigurierbar: nur durch Quelltextänderung.** Beide Mengen sind fest im Modul
notiert, es gibt keine Konfigurationsdatei und keine Umgebungsvariable. Eine Zeile in
`READ_ONLY_MCP_TOOLS` würde `aiimaging_query_render` und `aiimaging_check_geometry`
freischalten. **Das ist eine Sicherheitsentscheidung in fremder Lane; wir ändern sie
nicht, wir beantragen sie.**

Zwei Dinge, die der Bericht nicht erwähnt und die dazugehören:

- **Der Aufruf reicht ungefiltert durch.** In `run_pipeline_node` steht
  `mcp_manager.call_tool(tool, {**inputs, **arguments})` — alle Felder aller Vorgänger
  landen beim Werkzeug, ohne Abgleich mit dem Eingabeschema. Deshalb dürfen unsere
  Eingabeschemata **nicht** `additionalProperties: false` setzen; sonst weisen wir
  Aufrufe ab, die das Cockpit für gültig hält. (Das steht in unserem
  `EINBINDUNG_KOSMOORBIT`-Papier bereits als Konvention — hier ist der Grund im
  Quelltext bestätigt.)
- **Selbst ein lesendes Werkzeug bleibt gesperrt, wenn der Aufrufer ein API-Token
  benutzt** statt einer Sitzung im Browser (`getattr(request.state, "api_token", False)`).
  Für eine Demo, die jemand vor dem Bildschirm vorführt, ist das folgenlos; für einen
  automatisierten Aufruf nicht.

### 2.4 Der Befund, der schwerer wiegt als alle drei: das Cockpit sieht unsere Schemata nicht

Der HomeStation-Bericht hat am laufenden Backend gemessen: 31 Werkzeuge, **31 ohne
`input_schema.properties`, 31 ohne `output_schema`**. Das Cockpit liest die Felder
korrekt aus (`kosmo.ts`, Zeilen 358–359), bekommt aber nichts zu lesen.

Ich habe die Gegenprobe im Quelltext gemacht, und sie ist **widersprüchlich**: Die
Sicherungskopie von `mcp_manager.py` erfasst Ein- und Ausgabeschema an allen drei
Verbindungswegen (stdio, SSE, HTTP) und gibt sie in `get_all_tools()` weiter. Nach
*dieser* Fassung dürfte die Messung nicht herauskommen. **Entweder läuft auf der
HomeStation eine andere Fassung, oder die Schemata gehen an einer Stelle verloren, die
in der Sicherungskopie nicht enthalten ist.** Das ist keine Kleinigkeit, sondern die
Frage, ob unsere Verdrahtungsprüfung überhaupt je greifen kann — und sie ist **offen**.

Warum das für die Demo zählt: `nodeReadinessIssues` steigt ohne Schemata an zwei
Stellen früh aus (`if (!required.length) continue`, `if (!sOut.length || !tIn.length)
continue`). Ergebnis: keine Meldung — weder über eine tote Kante noch über eine lebende.
Das Ausführungstor filtert auf `severity === 'error'` und findet nie eines. **Eine
Pipeline, die nicht verdrahtet ist, sieht im Cockpit genauso aus wie eine, die es ist.**

---

## 3 · Gibt es schon eine Knotenoberfläche?

**Ja — `src/components/NodePipeline.tsx` im Cockpit, 1 120 Zeilen, auf xyflow.**
Aber sie ist ein anderes Werkzeug als das, was die Demo-Vision beschreibt.

### 3.1 Was sie kann

Ein Knoten ist ein Kästchen mit einem Eingang links und einem Ausgang rechts. Sein
Datensatz (`KData`) trägt: eine Kategorie, Titel, Untertitel, optional ein
**MCP-Werkzeug**, eigene Argumente, ein optionales **Gate** und ein optionales
**Transform**.

Es gibt **sieben Kategorien** — sie sind reine Farbgebung, keine unterschiedliche Logik:

| Kategorie | Anzeige |
|---|---|
| `manuell` | Manuell — ein Knoten, in den man Werte von Hand einträgt |
| `pnmanuell` | PN-Manuell |
| `pna` | PNA — deterministischer Rechenschritt |
| `agent` | KI-Agent |
| `memory` | KI-Erinnerung |
| `generator` | KI-Generator |
| `ak` | AK — ein ganzes Nachbarsystem als ein Kasten |

Für die **Ausführung** kennt das Backend genau **einen** Knotentyp: `mcp_tool`. Alles
andere beantwortet `run_pipeline_node` mit „Unsupported ntype".

### 3.2 Wie Kanten gebildet werden — beides, und das ist der Kern

Die Frage aus dem Auftrag („Feldnamen-Gleichheit oder explizite Verbindungen?") hat eine
zweiteilige Antwort, und die Zweiteilung ist der wichtigste Satz dieses Kapitels:

> **Die Kante wird von Hand gezogen. Ob durch sie etwas fliesst, entscheidet die
> Gleichheit der Feldnamen — und niemand meldet, wenn nichts fliesst.**

- **Explizit** ist die Verbindung: Der Benutzer zieht sie mit der Maus (oder ein Rezept
  legt sie an). Sie bestimmt allein die **Reihenfolge** (topologische Sortierung, Kahn)
  und das **Überspringen** bei Fehlern.
- **Über Feldnamen** läuft der **Datenfluss**: `mergeInputs` legt schlicht die Ausgaben
  **aller** Vorgänger übereinander (`Object.assign`) und reicht das Ganze weiter. Ein
  Wert kommt beim Nachfolger nur an, wenn dessen Eingabefeld **genau gleich heisst**.

Für den zweiten Teil gibt es eine Synonymtabelle, `FIELD_ALIAS_GROUPS`. Sie hat
**drei Gruppen, und alle drei betreffen Flächen und Ausnützungsziffer**:

```
['parzelle_flaeche_m2', 'landflaeche_m2', 'site_area_m2']
['az', 'az_limit', 'max_az']
['total_hnf_m2', 'programm_hnf_m2']
```

**Nichts davon betrifft Dateipfade.** Unser `glb_path` oder `ifc_path` trifft also nur
auf ein exakt gleichnamiges Feld — was in unserem `contracts.py` (`LANE_FIELDS`) bereits
richtig berücksichtigt ist.

Die Entwurfszeit-Prüfung `nodeReadinessIssues` kennt drei Beanstandungen:
`missing-required` (Fehler, wird zu Warnung herabgestuft, sobald ein Vorgänger kein
Ausgabeschema hat), `dead-edge` (Warnung) und `alias-conflict` (Warnung). Nur `error`
blockiert. Ohne Schemata (§2.4) meldet sie nie etwas.

### 3.3 Was es an „vorverdrahteten Presets" gibt

`src/lib/recipes.ts` führt **18 Rezepte** — vorgefertigte, lauffähige Ketten. Das
Ladeverfahren ist bemerkenswert schlicht und für uns wichtig:

1. Ein Konfigurationsknoten wird angelegt (trägt z. B. `project_dir`).
2. Jeder Rezeptschritt wird ein Knoten, der Werkzeugname wird zur Laufzeit auf die
   qualifizierte Form mit Kennung aufgelöst. Fehlt ein Werkzeug, bricht das Laden mit
   einer Meldung ab.
3. Der Konfigurationsknoten wird an **jeden** Schritt gehängt (Fächer), damit die
   gemeinsamen Angaben alle erreichen.
4. Nur bei ausdrücklich als „verkettet" markierten Rezepten werden zusätzlich Kanten
   Schritt *i* → *i+1* gezogen.

Ein Rezept `entwurf` („Prepare→Design→Vis→Publish") existiert und enthält als
Vis-Schritt `kosmovis_query_comfyui_status` — also nur die Frage *„ist das
Render-Backend bereit?"*. Der Kommentar dazu sagt ausdrücklich: der eigentliche
Render-Auftrag und die Geometrie-Naht seien „die tiefere Naht" und bewusst nicht im
Rezept. **Das ist genau die Lücke, in die unsere Lane gehört.**

### 3.4 Der Abstand zur Demo-Vision

Die Vision beschreibt Knoten für **Prompter, 3D-Kamera, Bildstil, AI-Imaging,
Rendereinstellungen, Kompositor, Material- und Farbebenen** und einen Ausgabeknoten
**„start imaging"**, der Varianten erzeugt.

| Element der Vision | Im Cockpit vorhanden? |
|---|---|
| Knotenoberfläche mit Ziehen/Verdrahten | **ja** |
| Vorverdrahtete Presets | **ja**, als 18 Rezepte — aber keines davon bildbezogen |
| Knoten „Prompter" | nein |
| Knoten „3D-Kamera" | nein |
| Knoten „Bildstil" | nein |
| Knoten „AI-Imaging" | nein |
| Knoten „Rendereinstellungen" | nein |
| Knoten „Kompositor" | nein |
| Knoten „Material-/Farbebene" | nein |
| Ausgabeknoten „start imaging" mit n Varianten | nein |
| Bildvorschau am Knoten | **teilweise** — es gibt Zusatzanzeigen im Ausklapp-Bereich (Plan, BIM-Ebenen, Varianten, GLB-3D), aber keinen Bild-Kachel-Typ |
| Anzeige eines QA-Werts je Bild | nein |
| „Visualisierungsprojekt erstellen" | nein — Pipelines werden im Browser-Speicher unter einem Namen abgelegt, es gibt keinen Projektbegriff |

**Die ehrliche Zusammenfassung:** Der *Rahmen* der Vision steht — ein Knoten-Editor mit
Ausführung, Fehlerbehandlung, Gates, Speichern und Laden. Der *Inhalt* fehlt vollständig.
Die vorhandenen Knoten sind Werkzeugaufrufe an Fachanwendungen (Zonenplan, Flächen,
Plan-Lint), nicht Bildparameter. Ein Knoten „Bildstil" mit einem Schieberegler ist im
heutigen Modell nicht ausdrückbar: Ein Knoten hat **ein** Werkzeug und **ein**
Argument-Objekt, keine typisierten Bedienelemente.

### 3.5 Was es stattdessen an einer bedienbaren KosmoVis-Oberfläche gibt

Und hier liegt der zweite grosse Befund dieser Sitzung.

Die **Designzentrale** (`Architektur-Cosmos/kosmo-orbit/`) hat ein fertiges
KosmoVis-Panel: `apps/kosmo-orbit/src/modules/vis/VisWorkspace.tsx`, 230 Zeilen. Es
zeigt heute schon:

- ein Feld für die Adresse der HomeStation-Brücke, mit Ampel „online / offline",
- einen **Schieberegler „Geometrie-Treue"** (0…1),
- ein Textfeld für den **Stil-Prompt**,
- einen Knopf „Render-Job senden" — er exportiert das Modell als glb und schickt es
  zusammen mit einer `render-scene` an `POST /jobs`,
- eine Liste der Aufträge mit Status,
- **und je fertigem Auftrag: die Bilder, ein Abzeichen „QA bestanden / verfehlt", den
  Geometrie-Treue-Wert mit der Schwelle 0.65 und den Stil-Wert mit der Schwelle 0.30.**

Das ist — für ein einzelnes Bild — **fast genau der Ausgabeknoten, den die Demo-Vision
in Weg A verlangt.** Der Vertrag dahinter liegt in
`packages/kosmo-contracts/src/render-scene.ts` (`kosmovis.render-scene/v1`) und
`render-result.ts` (`kosmovis.render-result/v2`), beides als prüfbare Schemata.

Es fehlen: mehrere Kameras (`cameras: 'auto'` ist fest verdrahtet), Varianten, ein
QA-Block **pro Kamera**, und die Knotenform. Und: dieses Panel spricht **nicht** MCP,
sondern eine eigene HTTP-Schnittstelle. Es ist ein **zweiter, unabhängiger Weg** zu
unserer Lane.

---

## 4 · Was unsere Lane braucht, um in der Demo zu erscheinen

Zwei Wege führen hin. Sie schliessen einander nicht aus, aber sie kosten verschieden
viel und liegen verschieden weit in fremdem Gebiet.

> **Legende:** 🟩 = liegt in **unserem** Repo · 🟥 = liegt in einem **fremden** Repo, dort
> ändern wir nichts ohne Rückfrage (CLAUDE.md, Abschnitt Git)

### Weg A — über das Cockpit (MCP-Knoten)

| # | Schritt | Wo |
|---|---|---|
| A1 | `mcp<2` in `pyproject.toml` festschreiben. Der Server ist gegen die 1.x-Schnittstelle geschrieben; `mcp` 2.0.0 hat `list_tools`/`call_tool` von `Server` entfernt, und jeder frische Rechner installiert heute die kaputte Kombination. | 🟩 |
| A2 | Den Ausgabeschema-Bruch in `aiimaging_query_render` beheben (`None`, wo ein String zugesagt ist). Solange er besteht, fällt der Knoten im Cockpit auf „Fehler". | 🟩 |
| A3 | Prüfen, ob unsere Eingabeschemata irgendwo `additionalProperties: false` setzen — sie dürfen es nicht (§2.3). | 🟩 |
| A4 | **Klären, warum `/api/mcp/tools` keine Schemata durchreicht** (§2.4). Ohne diese Antwort ist jede Verdrahtungsprüfung im Cockpit folgenlos, und wir bauen ins Blaue. Erst messen, dann melden. | 🟥 Odysseus-Backend |
| A5 | Eintrag von `aiimaging_query_render` und `aiimaging_check_geometry` in `READ_ONLY_MCP_TOOLS` **beantragen** — mit Begründung, warum sie nicht mutieren. `aiimaging_enqueue_render` **nicht** beantragen: Es schreibt eine Auftragsdatei und gehört zu Recht hinter die Sperre. | 🟥 Odysseus-Backend (Sicherungskopie im Codex-Repo) |
| A6 | Ein **Rezept** „AI-Imaging" in `RECIPE_META`/`RECIPE_STEPS` beantragen: Konfigurationsknoten → `check_geometry` (mit Gate auf `entscheidung`) → `enqueue_render` → `query_render`. Das Gate-Muster gibt es bereits fertig (`render_preflight`) und es passt exakt auf unsere Torwächter-Logik. | 🟥 Cockpit |
| A7 | Feldnamen gegenprüfen: Liefert der vorgesehene Vorgänger (`kosmodraw_export_glb` → `glb_path`, `up_axis`) genau die Namen, die unser `inputSchema` verlangt? `LANE_FIELDS` sagt ja; nach A4 lässt es sich zum ersten Mal auch **messen**. | 🟩 messen, 🟥 belegen |
| A8 | Für Weg A der Demo-Vision (QA sichtbar): Es gibt im Cockpit **keinen Ort**, an dem ein Bild und ein Wert am Knoten erscheinen. Entweder ein neuer Ausklapp-Typ im Cockpit (fremd), oder die Demo zeigt die QA in der Designzentrale (§3.5). **Das ist eine Owner-Entscheidung, keine technische.** | 🟥 / Entscheid |

### Weg B — über die Designzentrale (HTTP-Brücke)

| # | Schritt | Wo |
|---|---|---|
| B1 | Unseren `aiimaging.render-scene/v1`-Vertrag gegen `kosmovis.render-scene/v1` halten und die Unterschiede an **einer** Stelle übersetzen — dasselbe Muster wie `kosmo_naht.py` und `gate.als_kosmovis_verdikt`. Konkret abweichend: deren `geometry.path`+`format` gegen unser `geometry.ifc_path`/`glb_path`; deren `render.faithful`, `style.mode/refs/prompt`, `vis.backbone/upscale`, `cameras: 'auto'|'saved'|[…]`. | 🟩 |
| B2 | Den **Kameravertrag** angleichen. Deren `CameraSpec` heisst `name`/`position`/`target`/`fov`; unser `kameras.py` führt `blick_auf` und Brennweite in mm. Beides ist ineinander umrechenbar, aber die Namen müssen an der Naht stimmen. | 🟩 |
| B3 | `kosmovis.render-result/v2` erzeugen: `job_id`, `images`, `qa.style`, `qa.geometry`, `qa.verdict` — mit den Feldnamen `style_score`, `geometry_fidelity`, `spearman`, `geom_iou`, `threshold`, `passed`. Unser `gate.als_kosmovis_verdikt` deckt das teilweise ab; `spearman` und `geom_iou` einzeln auszuweisen ist neu. | 🟩 |
| B4 | Der **Arbeiter fehlt auf beiden Seiten.** Die Brücke legt nur Dateien ab (`job.json`, `render-scene.json`, `model.glb`) und wartet, dass jemand `render-result.json` daneben legt. Genau das tut unser `tools/homeworker.py` heute für unsere eigenen Auftragsdateien. Ihn auf das fremde Verzeichnisformat zu erweitern ist **die kleinste denkbare Naht zur Demo** — und sie liegt vollständig bei uns. | 🟩 |
| B5 | QA **pro Kamera** ausweisen, nicht pro Bild, und die Verzeichniskonvention `<out>/<kamera>/render_<kamera>_<pass>.png` bedienen. | 🟩 |
| B6 | Varianten: Die Vision verlangt *n* Bilder je Lauf. Weder unsere Kette noch die fremden Verträge kennen heute Varianten (`images` ist zwar eine Liste, aber niemand füllt sie mit Varianten desselben Blickwinkels). | 🟩 zu entwerfen |
| B7 | Falls die Demo diesen Weg nimmt: Der Schieberegler „Geometrie-Treue" im Panel schickt `render.faithful` — der Treue-Regler, den es beim alten Vorgabe-Backbone gar nicht gab. Nach dem Backbone-Entscheid (`docs/BACKBONE_CONTROLNET_2026-08-18.md`) ist er real; die Naht muss ihn durchreichen. | 🟩 |

### Die Empfehlung in einem Satz

**Weg B ist deutlich kürzer und liegt fast vollständig bei uns** — sechs von sieben
Schritten sind eigenes Gebiet, es gibt bereits eine bedienbare Oberfläche mit
QA-Anzeige, und der einzige fremde Bestandteil (die Brücke) ist ein Dateiverzeichnis,
das wir bedienen statt ändern. **Weg A ist der architektonisch richtige** — er ist der
Vertrag, auf den unsere ganze MCP-Schicht ausgelegt ist —, aber er hängt an einem
ungeklärten Backend-Befund (A4) und an zwei Bitten in fremde Lanes (A5, A6).

Das ist keine Empfehlung, Weg A fallenzulassen. Es ist die Feststellung, dass **die Demo
nicht davon abhängen sollte, dass eine fremde Lane rechtzeitig eine Zeile einträgt.**

---

## 5 · Lizenzbefunde (Regel 1)

Alles Folgende ist **ausdrücklich gemeldet**, auch wo es folgenlos scheint.

### 5.1 Keine neuen GPL- oder AGPL-Funde im Cockpit

Die Suche nach `GPL`, `AGPL`, `GPL-3`, `GNU General Public` und `LGPL` im gesamten
Cockpit-Quelltext ergibt **keinen Treffer**. Die deklarierten Abhängigkeiten sind
durchweg permissiv (React, xyflow, Radix, Tauri, Vite, Ajv, Tailwind, framer-motion,
`@google/model-viewer`).

**Einschränkung, die dazugehört:** Ich habe die **deklarierten** Namen in `package.json`
gelesen, nicht die tatsächlichen Lizenzdateien der installierten Pakete — die Pakete
sind hier nicht installiert. Das ist eine Sekundärquelle im Sinne unseres Lexikons. Für
eine belastbare Aussage müsste `npm ci` laufen und die Lizenzen am Original geprüft
werden.

### 5.2 Bereits bekannte GPL-Komponenten, unverändert gültig

Zur Vollständigkeit, weil eine Bestandsaufnahme sie nennen muss: **Blender**
(GPL-2.0-or-later, Binärfassungen GPL-3.0-or-later), **IfcOpenShell**
(LGPL-3.0-or-later, das Wheel bindet **CGAL** unter GPL-3.0-or-later statisch ein). Beide
erreichen unser Produkt ausschliesslich über die Prozessgrenze und stehen im `NOTICE`.
**Kein neuer Befund, keine Änderung.**

Die Konzept-Karte des Cockpits führt in der KosmoVis-Spur einen Knoten „ComfyUI-Bridge"
als *gebaut*. **ComfyUI steht unter GPL-3.0.** Für uns ändert das nichts — es ist ein
fremder Bestandteil in einer fremden Lane, und unsere Lagebeurteilung hat ComfyUI aus
genau diesem Grund ausgeschlossen. **Es ist aber der Beleg dafür, dass die
Bildpipeline des Ökosystems heute auf einer GPL-Komponente steht**, und das gehört
gesagt, bevor jemand vorschlägt, sie „einfach zu verwenden". (Die GPL-3.0-Einstufung
von ComfyUI ist bei uns primärquellenbelegt — `docs/LAGEBEURTEILUNG_2026-08-14.md`,
Zeile 37, LICENSE-Datei am Original geprüft.)

### 5.3 Drei proprietäre Fundstücke — kein Copyleft, aber eine harte Grenze

| Fund | Lizenz | Folge |
|---|---|---|
| **Cockpit** (`Imperigo/KosmoOrbit`) | **keine LICENSE-Datei** → alle Rechte vorbehalten | Wir dürfen daraus **keinen Code übernehmen**. Lesen ja (der Owner hat Zugriff erteilt), kopieren nein. Verträge und Feldnamen sind **Tatsachen, kein Werk** — die dürfen wir bedienen. |
| **Designzentrale** (`kosmo-orbit/`) | `"license": "UNLICENSED"`, README sagt „Proprietär" | dasselbe |
| **Odysseus** (das Backend) | **unbekannt** | siehe unten |

**Der Odysseus-Befund ist der einzige, der wirklich offen ist.** Das Backend, das die
MCP-Registrierung, das Read-only-Tor und die Werkzeugliste betreibt, ist ein fremdes
Produkt aus `github.com/pewdiepie-archdaemon/odysseus`, gespiegelt am Commit
`0e6cbd83…` vom 02.06.2026. **In keinem der geprüften Repos steht eine Lizenzangabe
dazu**, und das Repo ist von hier aus nicht erreichbar (403 bzw. keine Treffer). Der
Entscheid `0002-odysseus-as-kosmo-desktop-v2-base.md` behandelt Rolle, Sicherheit und
Integration ausführlich — die Lizenz erwähnt er mit keinem Wort.

**Warum das trotzdem kein akutes Problem für uns ist:** Odysseus ist ein separater
Serverprozess. Wir importieren nichts davon, wir bündeln nichts davon, wir sprechen
HTTP mit ihm. Das ist dieselbe Aggregation wie bei Blender. **Warum es trotzdem
gemeldet gehört:** Wäre Odysseus AGPL, hätte das Folgen für **denjenigen, der es
betreibt** — und wenn das ausgelieferte Produkt später einen Odysseus mitbringt, ist es
unser Problem. Solange wir nur einen bereits laufenden Odysseus **benutzen**, ist es
das des Betreibers.

**Empfehlung:** Die Lizenz vor der Demo klären und in `NOTICE` aufnehmen, sobald sie
bekannt ist. Ich habe `NOTICE` nicht geändert — eine unbekannte Lizenz einzutragen wäre
schlimmer als der Fehlbestand.

### 5.4 Ein Regel-3-Fund in fremdem Gebiet

Die Rezeptdatei des Cockpits trägt in mehreren Argumenten **fest verdrahtete
persönliche Home-Verzeichnispfade** eines Benutzerkontos. Ich gebe sie hier nicht
wieder (Regel 3 gilt für unsere Ausgaben). Es ist ein fremdes Repo und keine Handlung
für uns — aber wenn wir je ein Rezept dorthin beantragen (Schritt A6), gehört es **ohne**
solchen Pfad formuliert.

---

## 6 · Was ich nicht prüfen konnte

Eine benannte Lücke ist mehr wert als eine überzeugend klingende Vermutung. Diese sind
offen:

1. **Was auf der HomeStation tatsächlich läuft.** Alle Backend-Aussagen dieser Datei
   stammen aus **Sicherungskopien** im Codex-Repo, ausdrücklich beschrieben als „Backup
   hier zur Reversibilität — live auf Platte unter `tmp/odysseus-vanilla/`". Der
   Widerspruch aus §2.4 (Kopie erfasst Schemata, Messung findet keine) ist damit nicht
   auflösbar. **Das ist die wichtigste offene Frage dieser Bestandsaufnahme.**
2. **Ob das Cockpit heute noch so aussieht.** `/workspace/kosmoorbit` steht auf
   `a69af5d` vom 14.08. Ob seither etwas dazugekommen ist, weiss ich nicht — ich habe
   bewusst nicht gefetcht, um nichts in einem fremden Klon zu verändern.
3. **Die Lizenz von Odysseus** (§5.3).
4. **Die tatsächlichen Lizenzen der Cockpit-Abhängigkeiten** (§5.1) — nur deklariert
   gelesen, nicht am installierten Original.
5. **Ob das KosmoVis-Panel der Designzentrale je gegen eine echte Brücke gelaufen ist.**
   Die Roadmap sagt „Render-Loop ✅", aber der Bridge-Test läuft mit `--fake-worker`,
   also ohne GPU und ohne echte Bilder. Ob unsere Kette dort andockt, ist damit
   **nicht** belegt.
6. **Die fünf grossen Klone jenseits des Gesuchten.** `Architektur-Cosmos` hat 5 114
   Dateien; ich habe darin gezielt nach der Oberfläche gesucht und den Rest (Website,
   Atlas-Daten, Skripte) nicht ausgewertet. Für die gestellten Fragen genügt das; für
   eine Aussage „im Ökosystem gibt es kein X" genügt es nicht.
7. **Die Rust-Seite** (`src-tauri`) beider Anwendungen — ungelesen. Sie ist für die
   gestellten Fragen ohne Belang, könnte aber Lizenzbefunde tragen.

### Nebenbefund zum Prüflauf

`python -m pytest -q` in unserem Repo: **2120 grün**, 31 Warnungen. Zweimal gelaufen,
beide Male dieselbe Zahl.

Der Auftrag nannte 2102. Die Differenz kommt **nicht** von mir. Beim Sitzungsbeginn lagen
uncommittete Änderungen an `src/aiimaging/kameras.py` und `tests/test_kameras.py` im
Arbeitsbaum; während dieser Sitzung sind sie als Commit `d1bc789` („Zwoelf gruene Zahlen,
zwoelf unbrauchbare Bilder") verschwunden, und eine weitere fremde Datei
(`docs/KI_MODULE_BESTAND_2026-08-19.md`) ist dazugekommen. **In diesem Repo arbeitet
offenbar parallel jemand anderes.** Das gehört ins Protokoll, weil es jede
Zahlenangabe aus dieser Sitzung relativiert.

**Ich habe genau eine Datei angelegt — diese — und nichts committet.**

---

## 7 · Was ins Lexikon gehört

Diese Begriffe kommen oben vor und fehlen in `docs/LEXIKON.md`. **Nicht selbst
eingetragen**, wie beauftragt:

| Begriff | Warum er gebraucht wird |
|---|---|
| **xyflow / React Flow** | der Baukasten, auf dem die Knotenoberfläche des Cockpits steht (MIT) |
| **Vite** | das Bauwerkzeug beider Oberflächen — gehört neben die vorhandenen Einträge React/TypeScript/Tauri |
| **Zod** | Bibliothek, mit der die Ökosystem-Verträge (`render-scene`, `render-result`) zugleich als prüfbarer Code und als Beschreibung existieren |
| **Monorepo / Workspace** | die Bauform der Designzentrale: mehrere Pakete in einem Repo, die einander benutzen |
| **localStorage** | der Browser-Speicher, in dem das Cockpit Pipelines ablegt — erklärt, warum es dort keinen Projektbegriff gibt |
| **Allowlist / Denylist** | das Sicherheitsmuster hinter `READ_ONLY_MCP_TOOLS`; „Fail-closed" steht schon drin, die Liste selbst nicht |
| **Topologische Sortierung** | wird zweimal erwähnt, aber nirgends erklärt: die Reihenfolge, in der Knoten laufen dürfen, damit jeder seine Vorgänger schon hinter sich hat |
| **Fächer / Fan-out** | eine Quelle speist mehrere Ziele — das Ladeverfahren der Rezepte |
| **Preset / Rezept (Pipeline)** | eine vorgefertigte, ladbare Knotenkette; zentral für die Demo-Vision |
| **Gate (im Knotengraph)** | ein Knoten, dessen Ergebnisfeld darüber entscheidet, ob die nachfolgenden Knoten überhaupt laufen — bei uns die natürliche Landestelle des Torwächters |
| **Tote Kante** | eine gezogene Verbindung, durch die kein einziges Feld fliesst, weil kein Name übereinstimmt |
| **systemd / Dienst-Neustart** | kommt in der Merkregel „nach dem Registrieren neu starten" vor |
| **Server-Kennung (MCP)** | die vom Backend vergebene Kurzkennung, die im qualifizierten Werkzeugnamen steht — Ursache eines ganzen Kapitels im HomeStation-Bericht |
