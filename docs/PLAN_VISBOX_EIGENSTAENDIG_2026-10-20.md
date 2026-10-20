# Visbox eigenständig — die Oberfläche aufs Gerät, der Heim-PC als Rechenserver (Plan, 20.10.2026)

**Stand:** Owner-Auftrag 20.10.2026 über LW, wörtlich *«gut dann baue nächste version richtig!»* — kein Plan zur
Abnahme, sondern Bau ab sofort (Fassung 0.3.x). Die Fragen in §9 gehen gebündelt an den Owner; bis zur Antwort gilt
jeweils die **Empfehlung als Annahme** (steht so im Fassungsblatt). Schritt 1 ist in Arbeit.
**Anlass:** Owner-Entscheid 20.10.2026 über LW, wörtlich:

> *«eigendlich will ich nur den renderauftrag für blender und llm lokal auf home pc haben … kosmoorbit läuft ja auch auf
> dem installierten gerät und sendet nur aufträge wie llm und render aufträge an home pc»*

und die Präzisierung desselben Tages:

> *«visbox ist eine standalone lokale software die theoretisch wenn der laptop genug leistung hat blenderrender selbst
> machen kann und wenn sogar genug llm leistung da wäre sogar das lokale llm auch auf laptop laufen könnte … home pc ist
> eigentlich nur server wo sich visbox verknüpft um die heavy arbeiten übernehmen zu können für laptop»*

## 1 · Was heute wo läuft (erhoben, Prüfweg: Quelltext gelesen)

| Teil | Heute | Beleg |
|---|---|---|
| Mac-App | Natives Fenster (Start, Koppeln, Vorführmodus, Assistent-Leiste) **plus ein Webfenster**, das Knotenansicht (`/knoten/`) und Visbox-Seite (`/`) **vom Heim-PC lädt** (Tailscale :8443 oder Heimnetz :8732) | `Start/Arbeitsansicht.swift:165-226`, `Kern/Flaechenwahl.swift:37-47` |
| Web-Inhalt im Mac-Bündel | **keiner** — nur Programm, Schriften, Icon, Beispielmappe | `.github/workflows/ipad.yml:192-207` |
| Knotenansicht (kosmovis dist) | 1,1 MB, mit relativen Pfaden gebaut (`base: './'`), also verschiebbar; spricht `./mappe`, `./graph`, `./modell.glb`, `./skizze`, `./modell-laden` und die Brücke `location.origin + '/bruecke'` | `kosmovis/apps/visbox-knoten/src/mappe.ts:96-330` |
| iPad-App | **ganz nativ**, kein Webfenster. Holt Mappe und Bilder vom Heim-PC (`/api/projekt`, `/bild`), schickt Skizzen und Bestellungen (`/api/skizze`, `/api/rechne`) | `Kern/Vermittlung.swift:169-171`, `Kern/Anfragen.swift` |
| Mappe (Modell, Bilder, Skizzen, Knotengraph) | **nur am Heim-PC**; die Geräte halten nichts, ausser dem Parkfach des iPad für ungesendete Skizzen | `projekt.py:99`, `Parkfach.swift` |
| Rendern | zwei Wege: `/api/rechne` **im Serverprozess** (Seite, iPad) und `/bruecke/jobs` → Abholer als **eigener Prozess** (Knotenansicht, RenderJob-Vertrag) | `server.py:2700-2746`, `abholer.py:1787` |
| Assistent | am Heim-PC: `/api/assistent` → `aiimaging.assistent` → Ollama `qwen3:30b` | `server.py:2759-2803`, `assistent.py:113-128` |
| Ohne Heim-PC | Mac zeigt den **Vorführmodus** statt der Arbeit; die ganze Weboberfläche ist weg | `Hauptfenster.swift:48-51`, `Vorfuehrschalter.swift` |

**Zum Vergleich KosmoOrbit:** Die Oberfläche steckt im Programm (Tauri, `frontendDist` im Binary), das Projekt liegt am
Gerät (IndexedDB). Je Auftrag gehen Modell und `render-scene.json` als `POST /jobs` an die Brücke des Heim-PC, Bilder
kommen über `GET /jobs/{id}/artifacts/{name}` zurück, der Stand wird abgefragt (alle 2,5 s). Die Brücke hält kein
Projekt, nur einen Ordner je Auftrag. Das Sprachmodell geht über `/llm/*` (bzw. `/bruecke/llm`) unverändert an Ollama
durch, mit `X-Kosmo-Token`.

## 2 · Das Ziel in fünf Sätzen

1. **Visbox läuft ganz auf dem Gerät.** Knotenansicht, Mappe, Bilder, Einrichten und Assistent-Leiste kommen aus dem
   App-Bündel; der Heim-PC liefert keine Oberfläche mehr.
2. **Die Mappe liegt am Gerät** (Mac). Der Rechner bekommt je Auftrag nur, was er zum Rechnen braucht, und gibt die
   Bilder zurück — wie KosmoOrbit.
3. **Wer rechnet, ist austauschbar.** Je Arbeit (Blender-Render, Bildmodell, Bedien-KI) gibt es die Wahl «Heim-PC» oder
   «dieses Gerät». Vorgabe heute: Heim-PC. Beide sprechen denselben Auftragsweg (RenderJob-Vertrag), ein Rechner am
   Laptop ist später nur ein weiterer Abholer.
4. **Ohne Rechner bleibt alles bedienbar.** Nur Rechnen und Assistent sind gesperrt, mit einer klaren Zeile — kein
   Vorführmodus, der das Fenster ersetzt.
5. **Der Heim-PC ist ein Rechenserver:** Kopplung, Aufträge annehmen, Ergebnisse und Dateien abgeben, Sprachmodell.

## 3 · Was ins Bündel wandert, was am Heim-PC bleibt

| Ins Mac-Bündel | Bleibt am Heim-PC (Rechenserver) | Fällt am Heim-PC weg |
|---|---|---|
| kosmovis dist (Knotenansicht, 1,1 MB) | `GET /api/hallo`, `POST /api/verbinden`, `/api/kopplung*`, `GET /api/geraete` (Kopplung wie heute) | `GET /`, `/index.html` (Visbox-Seite) |
| Schriften (schon drin) | `/bruecke/health`, `/bruecke/jobs` (anlegen mit Modell, abfragen, freigeben, abbrechen), `/bruecke/jobs/{id}/artifacts/{name}` | `GET /knoten/*` (dist ausliefern) |
| Beispielmappe als **normale Mappe** (schon drin) | Bedien-KI: `/api/assistent` (vorerst) und neu `/bruecke/llm/*` als Durchreiche wie KosmoOrbit | `/knoten/mappe`, `/knoten/graph`, `/knoten/modell.glb`, `/knoten/skizze` (wandern ans Gerät) |
| Mappe-Verwaltung am Gerät (Ordner, Graph, Modell, Bilder) | Modell-Aufbereitung IFC → glb (`/knoten/modell-laden`) als **Auftrag**, weil IfcOpenShell am Heim-PC liegt (GPL, Prozessgrenze) | `/api/rechne` im Serverprozess (geht im Auftragsweg auf) |

**Wie das Webfenster ohne Heim-PC lädt:** Die Mac-App bedient die Knotenansicht über ein eigenes Adressschema
(`visbox://knoten/…`, WebKit-`WKURLSchemeHandler`): Dateien aus dem Bündel, `./mappe`, `./graph` usw. aus der Mappe am
Mac, `…/bruecke/*` gehen über die App an den gewählten Rechner (Kennwort aus dem Schlüsselbund). So bleibt die
Knotenansicht **unverändert** — KosmoOrbit und Visbox behalten denselben Knotencode.

**Was sich für die Updates ändert:** Die Knotenansicht kommt dann mit der Mac-App (Ein-Klick-Updater), nicht mehr mit
`git pull` am Heim-PC. Jede Knotenänderung braucht eine Mac-Freigabe. Die «Ansage an die HomeStation vor `main`» betrifft
dann nur noch den Rechenteil.

## 4 · Mappe und Bilder

**Vorschlag:** Die Mappe liegt am Mac (`~/Visbox-Mappen/<Name>/`, Aufbau wie heute `projekt.json`). Je Auftrag schickt
die App Modell (glb) und `render-scene.json`, wie KosmoOrbit; der Heim-PC rechnet in seinem Auftragsordner und behält
nichts Dauerhaftes. Die App holt die Bilder in die Mappe zurück. Eine wiederverwendete **Grundlage** (Nr. 85) bleibt am
Rechner liegen und wird mit ihrer Kennung angesprochen; fehlt sie dort, rechnet der Rechner sie neu (laut, nicht still).

**Das iPad:** heute holt es die Mappe vom Heim-PC. Vorschlag: Das iPad ist das Zeichenbrett **zum Mac** — es holt Mappe
und Bilder vom Mac (der Durchreich-Dienst am Mac besteht schon) und schickt Skizzen dorthin. Ohne Mac zeichnet es weiter,
Skizzen warten im Parkfach (wie heute).

**Bestehende Mappen am Heim-PC:** einmalig «an den Mac holen» (ein Knopf), danach liegt die Mappe am Mac.

## 5 · Rechner-Wahl

* Je Arbeit eine Zeile «Rechnet: Heim-PC ▾» (Blender-Render, Bildmodell, Bedien-KI). Ort: Einrichten, plus ein kurzer
  Hinweis am Render-Knoten.
* «Dieses Gerät» ist sichtbar, aber gesperrt mit Grund («kein Blender gefunden» / «zu wenig Grafikspeicher»), bis ein
  lokaler Rechner gebaut ist. Der lokale Rechner ist später derselbe Abholer (`aiimaging.abholer`) am Mac mit eigenem
  Auftragsordner — kein zweiter Weg.
* Bedien-KI: vor allem Claude über MCP (Owner). Das lokale Sprachmodell bleibt als Wahl möglich, ist zweitrangig.

## 6 · Abgleich mit KosmoOrbit

| Gegenstand | KosmoOrbit | Visbox heute | Visbox nach dem Umbau |
|---|---|---|---|
| Render-Auftrag | `POST /jobs` (RenderJob-Vertrag) | zwei Wege (`/api/rechne` und `/bruecke/jobs`) | **nur** `/bruecke/jobs`, derselbe Vertrag (inkl. R37-Fortschritt, Teilbild) |
| Ergebnisse | `GET /jobs/{id}/artifacts/{name}` | in die Mappe am Heim-PC | dieselbe Abfrage, in die Mappe am Mac |
| Sprachmodell | `/bruecke/llm` → Ollama, `X-Kosmo-Token` | `/api/assistent` (Logik am Heim-PC) | `/bruecke/llm` dazu; `/api/assistent` bleibt bis die Logik umgezogen ist |
| Anmeldung | Token, von Hand in Einstellungen | Kopplung mit Zahl/QR → Kennwort im Schlüsselbund | Kopplung bleibt; der Heim-PC nimmt zusätzlich `X-Kosmo-Token`, damit beide Programme denselben Rechner nutzen können |
| Ohne Heim-PC | alles bedienbar, ehrliche Meldungen | Vorführmodus ersetzt das Fenster | alles bedienbar, Rechnen/Assistent gesperrt mit Zeile |

## 7 · Reihenfolge und Aufwand (in Arbeitssitzungen)

| Schritt | Was | Aufwand | Danach gilt |
|---|---|---|---|
| 1 | Knotenansicht ins Mac-Bündel, Adressschema `visbox://`, Brücke durch die App (Mappe noch am Heim-PC durchgereicht) | 1–2 | Mac lädt keine Oberfläche mehr vom Heim-PC |
| 2 | Ohne Rechner: Zeile statt Vorführmodus; Beispielmappe als normale Mappe | 1 | Oberfläche ohne Heim-PC voll bedienbar |
| 3 | Mappe am Mac: Ordner, Graph, Modell, Bilder; Auftrag mit Modell hochladen, Bilder zurückholen; «an den Mac holen» | 3–4 | Heim-PC hält keine Mappe mehr |
| 4 | iPad holt Mappe und Bilder vom Mac, Skizzen an den Mac | 2–3 | iPad arbeitet mit dem Mac |
| 5 | Ein Render-Weg: `/api/rechne` auf den Auftragsweg; Seite und `/knoten/*` am Heim-PC abbauen; `/bruecke/llm` + `X-Kosmo-Token` | 2 | Heim-PC ist nur Rechenserver |
| 6 | Rechner-Wahl je Arbeit (Heim-PC aktiv, «dieses Gerät» vorbereitet) | 1–2 | Wahl sichtbar |
| später | Lokaler Rechner am Mac (Blender, ggf. Bildmodell, lokales Sprachmodell) | 3+ | «dieses Gerät» wählbar |

Zusammen rund **10–14 Sitzungen** bis Schritt 6. Jeder Schritt wird zuerst als Blatt auf der Entwurfsfläche gezeichnet
(Rechner-Zeile, Einrichten, «an den Mac holen»), dann gebaut; jeder endet mit einer Freigabe und einer Gerätprüfung.

## 8 · Was nicht geändert wird

* Lizenzregeln: Blender bleibt Prozess, IfcOpenShell bleibt hinter der Prozessgrenze — darum bleibt die
  IFC-Aufbereitung ein Auftrag an den Rechner.
* Der Kern bleibt die Python-Bibliothek (Regel 4); die Apps sind dünne Schichten darüber.
* Die Knotenansicht bleibt die Arbeitsfläche zum Rendern (E94) und bleibt mit KosmoOrbit derselbe Code.

## 9 · Entschieden (Owner, 20.10.2026, per Auswahl — alle wie empfohlen)

1. **Mappe am Mac** (103); der Rechner bekommt je Auftrag nur Modell und Szene.
2. **iPad holt die Mappe vom Mac** (103a).
3. **Vorführmodus entfällt** (103b); ohne Rechner normale Oberfläche mit gesperrtem Rechnen.
4. **Visbox-Seite kommt nicht in die App** (103c); was sie kann, wird Knoten (Blatt 25).
