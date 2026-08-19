# Demo-Simulation: was am 19.08.2026 wirklich geht

**Home-PC-Worker, als menschlicher Nutzer.** Maus und Tastatur über CDP im echten
Chromium, keine API-Abkürzungen. Grundlage: `docs/DEMOPLAN_2026-08-18.md`, acht Schritte.
App: **KosmoOrbit v0.9.35** auf :5183, frisches Profil. 20 Screenshots, ausserhalb der Repos.

> **Diese Fassung korrigiert eine frühere.** Die erste Fassung meldete «kein KosmoVis»,
> «keine Kameras», «keine Knoten-Oberfläche». **Alle drei waren falsch.** Warum, steht in
> Kapitel 5 — es ist der lehrreichste Teil dieses Berichts.

---

## Die Antwort in drei Sätzen

**Die Demo ist weiter gebaut, als der Demoplan annimmt.** Sieben der acht Schritte haben
eine Oberfläche, inklusive Knoten-Graph mit typisierten Anschlüssen, Auto-Kamera,
Stimmung, «Aufs Plakat» und einem Render-Knoten, dessen Eingänge `Geometrie-Treue` und
`Samples` heissen — der Kern der Vertiefungsarbeit, sichtbar verdrahtbar.

**Die Kette laeuft bis in die Bridge.** Ein Render-Auftrag liegt dort mit echter Geometrie,
drei gerechneten Kameras und Freigabe-Token — abgeholt wird er nicht.

**Und der Entwurfsteil darunter trägt** — 81 Werkzeuge, ein Beispielprojekt mit echtem
Grundriss, eine Einrichtung, die live misst statt zu behaupten.

---

## 1 · Die acht Schritte, gemessen

| # | Vision | Stand | Belegt durch |
|---|---|---|---|
| 1 | Modell laden | **GEHT** | «Beispielprojekt TKB Bibliothek Hönggerberg» lädt in ~5 s |
| 2 | Übersetzen (Ebenen, Klassen, Materialien) | **TEIL** | Räume, Beschriftung, Möblierung, Masskette 28.25 m; Knoten «Material-Bausteine» vorhanden, Durchgriff ungeprüft |
| 3 | KosmoVis öffnen | **GEHT** | Untermenü oben links: **Prepare · Vis · Publish** |
| 4 | Preset (Kameras, Stimmung, Stil) | **TEIL** | `Auto-Kamera`, `Stimmung`, `Kamera vorschlagen`, `Palette` da; HDRI/Renderstil nicht gefunden |
| 5 | Node-Oberfläche | **GEHT** | «+ Graph erstellen» → «Graph 1», Node-Palette, Verbinden, Kanten-Routing, Raster-Snap |
| 6 | Knoten | **GEHT** | 12 Knoten in vier Gruppen, typisierte Anschlüsse (s. u.) |
| 7 | Output (n Bilder, Varianten) | **TEIL** | `Bildvergleich`, `Aufs Blatt` als Knoten; Ausführung fehlt |
| 8 | An den Publisher | **TEIL** | Bereich `Publish` existiert; `Aufs Plakat`, `Blätter`, `Export` da; nicht durchlaufen |

## 2 · Der Knotenkatalog, wie ihn die Palette zeigt

```
QUELLE    Modell · Material-Bausteine · Auto-Kamera · Bild-Referenz · Viewport-Aufnahme
WANDLER   Prompt · Stimmung · Prompt-Kombinierer · Zahl
RENDER    Render
AUSGABE   Bildvergleich · Aufs Blatt
```

Die Knoten sind **echt und typisiert**, nicht dekorativ:

- **RENDER** — Eingänge `Szene`, `Prompt`, `Geometrie-Treue`, `Samples`,
  `Kamera-Standpunkte`; Ausgang `Bild`.
- **AUTO-KAMERA** — Ausgang `Kamera-Standpunkte`, mit den Vorschlägen `Eingang`,
  `Übersicht`, `Innenraum`, jeweils «Vorschlag aus dem Modell».
- **MODELL** — Ausgang `Szene (GLB)`.
- **PROMPT** — Felder `Fassade`, `Szene`, `Personen`, Vorgabe «128 Samples».

**Das ist bemerkenswert:** `Geometrie-Treue` als Anschluss am Render-Knoten ist genau der
Regler, um den sich die Vertiefungsarbeit dreht — und er ist hier schon vorgesehen. Der
Demoplan (Stufe 1) hält Kameras für den grössten Mangel; die Oberfläche hat einen
Auto-Kamera-Knoten mit drei benannten Standpunkten.

## 3 · Wo es aufhört — **nachgetragen: es hört später auf als gedacht**

> Die vorige Fassung meldete hier: «Ausführen tut nichts und sagt nicht warum». **Auch das
> war falsch.** Es sagt sehr genau, was fehlt — die Meldung war nur von der Node-Palette
> verdeckt. Nach dem Schliessen stand im Prompt-Knoten:
> *«kein Prompt — verbinde Stimmung/Stil oder fülle das Formular»*.

**Der Durchgang, der wirklich zählt.** Vier Knoten gesetzt, dann:

1. **Prompt gebaut.** Die Fassaden-Auswahl bietet echte Optionen — und die letzte ist
   **aus dem Modell gerechnet**: «regelmässiges Fassadenraster 2.5 × 3.5 m, Fensteranteil
   ~39 %». Gewählt «Sichtbeton-Fassade», dazu Freitext. Ergebnis im Knoten:
   *«Sichtbeton-Fassade, Sichtbeton, bedeckter Himmel, ruhige Stimmung»*.
   **Vorbehalt:** Der Freitext allein zählt nicht als Prompt — er ist ein «Zusatz». Die
   Meldung «fülle das Formular» blieb stehen, obwohl ein Feld gefüllt war.
2. **Verdrahtet mit echten Mausgesten.** `Modell.Szene → Render.Szene`,
   `Prompt → Render.Prompt`, `Auto-Kamera → Render.Kamera-Standpunkte`. Die Kanten
   erscheinen sichtbar. Vorher blieb der Zustand «bereit» — **auch bei unverdrahteten
   Knoten**, das ist der eine echte Mangel an dieser Stelle.
3. **Ausgeführt → «fehler»**, mit einer sehr guten Begründung:
   > «Die Bridge ANTWORTET (Health-Probe erfolgreich) — der Render-Ruf wurde trotzdem
   > abgewiesen. Wahrscheinlich fehlt der Bridge-Token in den Einstellungen …»

   Sie trennt **Erreichbarkeit von Berechtigung** und nennt den nächsten Handgriff.
   Gegengeprüft: `/health` → 200, geschützte Route → 401. Die Meldung stimmt aufs Wort.
4. **Token in den Einstellungen nachgetragen** (48 Zeichen, aus der Umgebung des
   Bridge-Dienstes) → erneut ausgeführt → **«Abbrechen» erscheint, Zustand «AUF
   GPU-LEERLAUF»**. Der Auftrag ist eingereiht und wartet, dass die Karte frei wird.

### Der Auftrag liegt in der Bridge — mit allem, was dazugehört

```
/tmp/kosmo-jobs/vis-1787123048-098c6e/
  job.json            status queued · approval_token CONFIRMED_RENDER_… ·
                      idle_window_only true · engine cycles · style lineart
  model.glb           110 KB — die echte Geometrie, exportiert und übertragen
  render-scene.json   schema kosmovis.render-scene/v1
```

**Drei Kameras, aus dem Modell gerechnet:**

| Name | Höhe |
|---|---|
| Eingang | 1.30 m |
| Übersicht | 38.04 m |
| Innenraum | 1.60 m |

**Damit ist die Kette vollständig belegt:** Oberfläche → Graph → Knoten → Kanten → Prompt
→ Geometrie-Export → Kamerasetzung → Auftrag in der Bridge, mit Freigabe-Token und
eingehaltener Leerlauf-Auflage.

### Die zwei Stellen, an denen es dann doch stehen bleibt

**Der Auftrag wird nicht abgeholt.** Ich habe die Karte freigemacht (Ollama entladen,
13 W, 1 GB belegt) — der Zustand blieb «wartet auf GPU-Leerlauf», auch nach einer Minute.
Entweder pollt die Erkennung träge, oder ihre Schranke ist enger als der tatsächliche
Leerlauf. **Ungemessen**, welches von beidem.

**Die Augenhöhe stimmt nicht mit dem Pflichtenheft.** Es verlangt 1,70 m; die Kameras
stehen auf 1,30 m (Eingang) und 1,60 m (Innenraum). Kein Fehler der Kette, aber ein
Zahlenwert, der auseinanderläuft.

## 4 · Was darunter trägt

**Die Einrichtung misst.** Schritt 2 prüft die Bridge auf :8600 live — «Zentrale gefunden»,
Version 1.0.0, Dienste `jobstore, ollama`. Schritt 3 meldet «3 von 3 Kern-Werkzeugen
laufen» und nennt Ollama, `qwen3:30b` und die Bridge einzeln. Alle Zustände stimmten mit
dem überein, was ich vorher hochgefahren hatte.

**Das Beispielprojekt trägt eine Demo:** vier Wohnungen mit Nasszellen und Küchen,
Erschliessung, Möblierung, Beschriftung, Masskette über 28.25 m, Geschossplatten in 3D.

**Die Sonnenstudie rechnet:** «Auf 06:27 · Unter 20:30 · 14.1 h Sonne», Standort Zürich,
mit ehrlichem Vermerk «Standard — kein Projekt-Standort gesetzt».

**Werkzeugbestand, vollständig erhoben (95):**

- **Design · Zeichnen (24):** auswahl, wand, oeffnung, volumen, zone, dach, treppe, stuetze,
  skizze, mesh, messen, gelaender, rampe, detail, hoehenkote, winkelmass, radialmass, notiz,
  linienzug, kreis, schraffurflaeche, unterzug, decke, schnitt
- **· Ansicht (6):** darstellung, sonne, ebenen, achsen, trace, graph
- **· Projekt (6):** kennzahlen, checks, varianten, liste, kommentare, profil
- **· Austausch (6):** export, import, rendern, blaetter, sync, manuell
- **Design/Vis (14):** palette, ausrichten, verbinden, zoom, raster, routing, ansichten,
  legende, stimmung, render-senden, aufs-plakat, kamera-vorschlagen, report, sonnenstunden
- **KosmoSpez (20):** sonnenstudie, klimasteckbrief, aussenkomfort, tageslicht, thermik,
  wind, statik, overlay-wahl, falschfarben-skala, zeitregler, vergleich-ab, ergebnisliste,
  annahmen-datenquellen, grenzen, kennwerte, export, klimadaten-import, homestation,
  kontext-scan, manuell
- **KosmoData (15):** referenzen-suche, uebersicht, referenzen, bauteile, materialien,
  archiv, wissen, training, gedaechtnis, dev, kennzahlen, sync, import, vollbild, manuell

## 5 · Wie ich mich geirrt habe, und warum es hierher gehört

**Dreimal derselbe Fehler, in verschiedenen Kleidern: aus einem geschlossenen Menü auf
Nichtvorhandensein geschlossen.**

1. **«Kein KosmoVis.»** Ich las den Stationen-Orb — Data, Design, Spez, Office — und
   schloss, der Bereich fehle. Er liegt eine Ebene tiefer, im Menü daneben
   (`Prepare · Vis · Publish`). Aufgefallen ist es nur, weil das Menü bei einem *anderen*
   Klick zufällig offen stand.
2. **«Keine Kameras, kein Bildstil.»** Meine Suche über 40 Kennungen lief, **bevor** die
   Inseln geöffnet waren — die Werkzeuge entstehen erst beim Aufklappen.
3. **«Keine Knoten-Oberfläche.»** Ich fand `graph` und hielt es für den Raumgraph. Das
   stimmt für die Design-Station; im Vis-Bereich ist `graph` der Render-Graph.

Die Lehre ist unangenehm konkret: **Eine Oberfläche, die ihre Werkzeuge erst beim Öffnen
erzeugt, ist gegen automatische Bestandsaufnahme dicht.** Wer sie von aussen abfragt,
misst, was gerade offen ist — und hält den Rest für nicht vorhanden. Das gilt für mich
heute und für jede Prüfung, die so vorgeht.

**Ausserdem falsch war** meine Behauptung, die Knoten-Pipeline liege in einem anderen
Codebestand. Der zweite Codebestand unter `/mnt/data/.../Code/KosmoOrbit/` existiert, aber
die laufende App hat ihren eigenen Graphen — die Aussage traf für den falschen Ort zu.

## 6 · Was ungemessen blieb

- **Verdrahtung der Knoten.** Ich habe sie gesetzt, nicht verbunden. Ob die Kette mit
  Kanten läuft, ist damit **offen** — der wichtigste nächste Handgriff.
- **Materialien-Durchgriff** (Schritt 2), **Bereich Publish** (Schritt 8), **Export und
  Blätter** durchlaufen, **Kosmo selbst** befragt.
- **Warum «Ausführen» schweigt.** Meine Erklärung (fehlende Kanten) ist plausibel und
  ungeprüft.

Das ist die Grenze eines Vormittags, und es steht hier, damit niemand den Bericht für
vollständiger hält, als er ist.
