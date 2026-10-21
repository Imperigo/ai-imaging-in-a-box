# Visbox eigenständig — die Oberfläche aufs Gerät, der Heim-PC als Rechenserver (Plan, 20.10.2026)

**Codestand:** `06b9872` (erhoben auf `claude/ai-imaging-assessment-pstkyp`; Schritt 1 gebaut: Protokoll 74 §146)
**Grundlage:** Quelltext gelesen (Prüfweg in §1); keine Messung
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

## 10 · Schritt 3 gebaut: die Mappe am Mac (21.10.2026, Protokoll 74 §174)

Vorlage: Blatt 28 Feld 3 und das neue Blatt 36 «Mappen am Mac» (`MappenAmMac.dc.html`). Gebaut nach Empfehlung:

* **Ordner** `~/Visbox-Mappen/<Name>/` mit `mappe.json` (`visbox.macmappe/v1`), `modell.glb`, `knotengraph.json`
  (dasselbe Format wie am Heim-PC), `heim/<weg>` (Skizzen und Bilder vom Heim-PC), `bilder/<auftrag>/` (Laufzettel
  und Bilder eines Auftrags). Regeln im Kern `Kern/Macmappe.swift` (Proben `MacmappeTests`).
* **Die Knotenansicht bleibt unverändert:** Ist eine Mappe am Mac offen, beantwortet die App `./mappe`, `./graph`
  (lesen und sichern), `./modell.glb` und `./skizze` selbst (`Knotenquelle`); `./standpunkte` geht mit dem Namen der
  Zwillingsmappe an den Heim-PC. Ohne offene Mappe am Mac geht alles wie bis 0.3.14 an den Heim-PC.
* **Auftrag mit Modell:** `POST /bruecke/jobs` trug das Modell schon immer (RenderJob-Vertrag). Neu nennt die App die
  Mappe (`X-Mappe-Am-Mac`, und `X-Mappe-Heim` für die Zwillingsmappe); der Heim-PC schreibt den Namen in den
  Laufzettel statt der Mappe, die dort zuletzt offen war, und rechnet eine Skizze in der Zwillingsmappe.
* **Bilder zurück:** Die App merkt sich jede Auftragskennung in `mappe.json`. Ist ein Auftrag fertig (`done`), holt
  sie seine Bilder (`result.images`) nach `bilder/<auftrag>/`; jedes Bild, das die Knotenansicht abruft, legt sie
  ebenfalls dort ab. Ohne Heim-PC kommen Laufzettel und Bilder aus der Mappe.
* **«An den Mac holen»:** Fenster «Mappen» (Palette am Logo «Mappen …», Menü ⌘O): «Am Mac» öffnen, «Noch am
  Heim-PC» holen (Liste, Paket, Datei für Datei; ein zweiter Klick holt nur, was fehlt), «Neue Mappe» anlegen, und
  «Ohne Mappe am Mac (wie bisher)». Die Beispielmappe ist eine gewöhnliche Mappe (Bilder ohne Modell).
* **«Datei laden …»** wandelt weiter am Heim-PC (IfcOpenShell bleibt dort, Regel 1); danach holt die App das Modell
  der neuen Mappe am Heim-PC in die **offene** Mappe am Mac (`POST ./mappe-holen`, nur die App kennt den Weg).

**Was nicht gebaut ist:** Das Modell bleibt je Auftrag ganz im Hochladen (keine Wiederverwendung über Aufträge
hinweg ausser der Grundlage, Nr. 85). Die Bilder der Beispielmappe zeigt die Knotenansicht nicht (sie liest nur
Auftragsbilder). Bilder, die am Heim-PC nur in der Mappe liegen (Visbox-Seite, `/api/rechne`), kommen beim Holen mit,
neue von dort aber erst mit einem neuen Holen — das endet mit Schritt 5.

## 11 · Schritt 4: das iPad holt die Mappe vom Mac (Entscheide 103a, 118)

**Gebaut am 21.10.2026 (Protokoll 74 §178, Einbau C106)** — mit Entscheid 118 (immer über den Mac, zuerst
verschlüsselt): TLS mit dem Zertifikat des Mac, Koppelschein Fassung 2 mit Fingerabdruck, Mappe/Bild/Skizze am Mac wie
in der Tabelle unten. **Abweichend von der Vorbereitung:** `rechne-skizze` geht mit Mappe am Mac **nicht** als Auftrag
an den Heim-PC, sondern sagt «gerechnet wird in der Knotenansicht» (Entscheid 94; keine Heim-PC-Änderung); die
Zwillingsmappe fällt darum noch nicht weg. Der Text darunter ist die Vorbereitung, wie sie stand.

**Heute (erhoben, Quelltext):** Das iPad spricht nur mit dem Heim-PC: `GET /api/projekt` (Mappe), `GET /bild?name=`
(Bilder, Skizzen), `POST /api/skizze` (Skizze ablegen), `POST /api/rechne-skizze` (Skizze rechnen), `GET
/api/fortschritt`, `GET /api/heim`. Die Wege stehen im Kern `Kern/Wege.swift` (`Weg.alle`), die Regeln in
`Kern/Anfragen.swift` und `Kern/Vermittlung.swift`. Unterwegs reicht der Mac sie unverändert an den Heim-PC durch
(`VisboxMac/Vermittlung/Vermittlungsdienst.swift`, Bonjour-Dienst der Marke mit `vermittler=mac`, nur wenn «iPad über
diesen Mac anbieten» an ist).

**Ziel:** Ist am Mac eine Mappe offen, beantwortet der Mac die Mappenwege des iPad **selbst** aus der Mappe am Mac
— dieselbe Rolle wie die `Knotenquelle` für die Knotenansicht. Alles andere reicht er weiter wie heute.

| Weg des iPad | Mit Mappe am Mac | Ohne Mappe am Mac |
|---|---|---|
| `GET /api/projekt` | **am Mac:** eine Antwort in der Form von `server.sicht` (Name, Bilder mit Titel und Urteil, Skizzen mit Stand), gebaut aus `mappe.json`, `heim/` und `bilder/<auftrag>/job.json` — neuer Kern-Teil `Macmappensicht` mit Proben gegen eine eingefrorene Antwort des Servers | Heim-PC |
| `GET /bild?name=` | **am Mac:** `heim/<name>` oder `bilder/<auftrag>/<name>`, Name nur aus der Sicht (dieselbe Pfadregel wie `bildpfad`) | Heim-PC |
| `POST /api/skizze` | **am Mac:** Skizze nach `skizzen/<stempel>.png`, Eintrag in `mappe.json` (`skizzen`, Stand «offen», Unterlage, Bemerkung) — die Knotenansicht sieht sie sofort über `./mappe` | Heim-PC |
| `POST /api/rechne-skizze` | **an den Heim-PC als Auftrag** `POST /bruecke/jobs` mit Modell, Szene **und der Skizze als Datei** (neues Formularfeld `skizze`, `knotenweg.lege_an` legt sie neben den Auftrag und rechnet ohne Mappe am Heim-PC); Bilder zurück wie in Schritt 3 | Heim-PC |
| `GET /api/fortschritt`, `GET /api/heim` | Heim-PC (Rechner) | Heim-PC |

**Reihenfolge:** (1) Kern `Macmappensicht` + `Mappenwege` für das iPad (welcher Weg am Mac bleibt) mit Proben;
(2) Heim-PC: Skizze als Formularfeld im Auftrag (`knotenweg.lege_an`, `abholer.skizzenlauf` ohne Mappe) mit Proben —
erst dann fällt die Zwillingsmappe weg; (3) Mac: `Vermittlungsdienst` fragt vor dem Weiterreichen die neue Regel;
(4) iPad: keine Änderung an den Wegen, nur der Satz «Mappe vom Mac» in der Startzeile, wenn der Vermittler `mappe=mac`
im TXT meldet; (5) Blatt auf der Entwurfsfläche vorher (Startzeile iPad, «Mappe vom Mac»).

**Offen zu entscheiden (mit Empfehlung):** Soll das iPad den Mac **auch zuhause** über die Vermittlung nehmen, sobald
eine Mappe am Mac offen ist? Empfehlung: ja — sonst sähe das iPad zuhause die Zwillingsmappe am Heim-PC und unterwegs
die Mappe am Mac, zwei Stände derselben Arbeit. Die Vermittlung ist heute unverschlüsselt (Entscheid 01.10.2026); vor
dem Bau braucht sie darum TLS mit dem Zertifikat des Mac (Kopplungsschein wie beim Heim-PC).
