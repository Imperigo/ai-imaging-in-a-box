# KI-Bedienung für Visbox — Claude über MCP und der Assistent mit denselben Werkzeugen (Plan, 20.10.2026)

**Codestand:** Plan, noch nichts gebaut; Visbox `98a30a5`, KosmoOrbit-Zweig `claude/kosmovis-vorschau`.
**Grundlage:** Entscheid 105 (Owner, 20.10.2026): *«Ja und alle Werkzeuge, voller Umfang freigeben von Funktionen für
Claude und für die KI-Assistenz. Übernimm sämtliche Funktionen von KosmoOrbit, was die KI-Bedienung angeht.»*
Bestandsaufnahme durch Lesen beider Repos (Protokoll 74, Sitzung vom 20.10.).

## 1 · Ist-Stand

**Visbox**
- MCP-Server `src/aiimaging/mcp_server.py` (stdio, MCP-SDK MIT, optional): vier Werkzeuge — Geometrie prüfen,
  Auftrag stellen, Auftrag abfragen, Fähigkeiten (`mcp_schemas.py:53-63`). Angemeldet nur bei Kosmos Hintergrunddienst
  am Heim-PC (`integrations/odysseus/`), **nicht bei Claude**.
- Assistent `src/aiimaging/assistent.py`: `qwen3:30b` über Ollama am Heim-PC, kleine Werkzeugschleife (3 Runden, drei
  Vorschlagswerkzeuge), keine Befehle an die Knoten; «Anwenden» **entlädt das Modell** (`keep_alive: 0`) und rechnet.
- Der Satz «Claude über MCP steuert Visbox immer» (`Kern/Rechnerwahl.swift:108`, seit 0.3.1) **stimmt nicht**.

**KosmoOrbit** (Vorlage)
- Claude schliesst an einen MCP-Server **in der App** an, nur `127.0.0.1:8630`, mit Host- und Origin-Prüfung
  (`tools/kosmo-mcp/src/kern.mjs`, `src-tauri/kosmo-mcp-kern/src/kern.rs`; `docs/CLAUDE-ANSCHLUSS.md`).
- Die Werkzeuge sind die Befehle des Kerns (`commandTools`, z. B. `vis_nodeSetzen`, `vis_verbinden`, `vis_render`),
  dazu `modell_lesen`, `kosmo_paket` (bis 40 Schritte, ein Rückgängig), `kosmo_blick` (Bild an Claude), `kosmo_maus`.
- Jede Änderung wird zuerst eine **Karte** (Vorschlag); Modi Karte / Coop / Vollautomatik (`state/kosmo-coop.ts`).
- Die GPU-Freigabe (`CONFIRMED_RENDER_…`) gibt im Knoten ein Mensch.
- Kosmos Modelle (`staffelung.ts:150ff`): Meister `kosmo-qwen3.6:35b-a3b`, **Leiter `qwen3:30b`**, Zeichner
  `qwen3-coder:30b`.

**Befund, der eine Regel berührt:** Der Visbox-Assistent nutzt `qwen3:30b` — dasselbe Modell wie Kosmos Leiter — und
entlädt es beim Anwenden. Die Owner-Regel sagt: Kosmo-Modelle werden nie entladen.

## 2 · Was übernommen wird

| Werkzeug (Vorlage KosmoOrbit) | Für Visbox |
|---|---|
| Knoten setzen, parametrieren, schieben, verbinden, trennen, einklappen, Graph anlegen (`vis_*`) | ja |
| Knoten und Graph löschen | ja, nur über Karte (Frage 4) |
| `vis_render` (Kamera, Stimmung, Modell, Grundlage, Startwert, Güte, Auflösung), `vis_varianten` | ja; GPU-Freigabe bleibt beim Menschen |
| `modell_lesen` → **`graph_lesen`** mit Knoten-Kennung, Typ, Ports, Parametern, Kanten, Läufen | ja, neu (behebt Nr. 54/61) |
| `kosmo_status`, Vorschlag-Status, Paket, Tätigkeitsstrom, Markierung, Modi | ja, als `visbox_*` |
| `kosmo_blick` (Bild an Claude), `kosmo_maus` (mit Sperrzonen, auch «Freigeben») | ja |
| Projekt anlegen / Bild ausgeben | ja als `mappe_anlegen`, `bild_exportieren` (Karte) |
| Wände, Decken, IFC-Bearbeitung, Publish, Normen, Geschosse, Docks | nein — Modellieren gehört zu KosmoOrbit |
| **Neu für Visbox:** `mappe_lesen`, `skizzen_lesen`, `modell_laden`, `kameras_vorschlagen`, `lauf_abbrechen`, `verlauf_lesen`, `bild_ansehen` | ja |

## 3 · Wie Claude anschliesst (Empfehlung)

MCP-Server **in der Mac-App**, nur auf diesem Rechner (`127.0.0.1:8631`), ohne fremde Pakete (Regel 1), ohne
Geheimnis in der Claude-Einstellung (Regel 3). Anschluss:
`claude mcp add --transport http visbox http://127.0.0.1:8631/mcp`, oder für Claude Desktop über `--mcp-stdio`.
Die Knotenansicht stellt die Werkzeuge bereit (derselbe Kerncode wie KosmoOrbit), die App reicht durch. Rechnen,
Prüfen und Kameras bleiben in der Python-Bibliothek am Rechner (Regel 4). Der Python-MCP am Heim-PC bleibt für Kosmo.

## 4 · Stufen

| Stufe | Inhalt | Sitzungen |
|---|---|---|
| 0 | Satz berichtigen; Kopie und KosmoOrbit-Zweig abgleichen (Varianten und Güte); Blatt 30 zeichnen | 1 |
| 1 | `ki-werkzeuge.ts` in beiden Programmen (Liste, `graph_lesen`, Karte, Anwenden, Paket) mit Proben | 2 |
| 2 | MCP-Kern in Swift mit Proben, Hörer nur lokal, `--mcp-stdio` | 2 |
| 3 | Brücke App ↔ Knotenansicht, Karten in der Assistent-Leiste, Tätigkeitsstrom, Einrichten | 1–2 |
| 4 | Mappe-, Skizzen-, Modell-, Kamera-, Abbruch- und Verlauf-Werkzeuge | 1–2 |
| 5 | Der Assistent bekommt dieselbe Werkzeugliste — **gebaut 21.10.2026** (Protokoll 74 §175) | 2 |
| 6 | Blick und Maus mit Sperrzonen; Coop und Vollautomatik — **gebaut 21.10.2026** (§175; Blatt «Blick und Maus») | 1–2 |
| 7 | Geräteprobe mit Claude Code und Claude Desktop; Fassungsblatt | 1 |

Zusammen rund **11–14 Sitzungen**. Stufe 4 ganz erst, wenn die Mappe am Mac liegt (Plan «Visbox eigenständig»,
Schritt 3).

## 5 · Zu entscheiden (Owner)

Entschieden 20.10.2026 per Auswahl, alle wie empfohlen: **106** Anschluss in der Mac-App, nur lokal; **106a** Karten
in der Assistent-Leiste; **106b** Karte als Vorgabe, Coop und Vollautomatik als Schalter, Grafikkarte immer durch einen
Menschen; **106c** Löschen nur über Karte. Offen: Modell des Assistenten (Kosmos Leiter `qwen3:30b`), Weg aus dem
Internet, Hinweis zu den Daten an Anthropic.

## 6 · Auftrag an KosmoOrbit (Nebenbefund)

Der Knopf «Freigeben» am Render-Knoten ist in KosmoOrbits Sperrzonen für `kosmo_maus` nicht enthalten — Claude könnte
dort die Grafikkarte freigeben. Geht an den Integrator.
