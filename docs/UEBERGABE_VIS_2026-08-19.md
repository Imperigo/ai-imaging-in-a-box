# Übergabeblatt an die Vis-Oberfläche

**19.08.2026 · geschrieben für den, der `KosmoDesign → Vis` baut · aiimaging-Lane**

---

## Wozu dieses Blatt

Wir bauen die Bildkette — Geometrie hinein, Tiefen- und Kantenbild daraus, daraus ein
gerendertes Bild, und darüber eine Qualitätsprüfung, die sagt, ob das Bild noch dasselbe
Gebäude zeigt. Ihr baut die Oberfläche, in der jemand auf **Ausführen** drückt.

Dazwischen liegt eine Naht. Dieses Blatt beschreibt sie und sonst nichts.

Es beschreibt sie **in Verträgen, nicht in Bildschirmen**. Das ist Absicht: Eure
Oberfläche entsteht gerade, unsere Kette auch, und wer die andere Seite nachbaut, baut am
Tag der Fertigstellung daneben. Ein Vertrag hält, während sich beide Seiten bewegen.

Drei Fragen, mehr steht hier nicht:

1. **Was schicke ich euch?**
2. **Was bekomme ich zurück?**
3. **Woran erkenne ich, dass eine Verbindung wirklich trägt?**

Die dritte ist die wichtigste, und sie steht am Schluss.

---

## 1 · Was ihr uns schickt

Es gibt zwei Wege hinein. Beide sind gebaut und geprüft. **Ihr müsst euch nicht
entscheiden** — sie führen auf dieselbe Kette, und wir bedienen beide.

### Weg A — Der Szenenvertrag (Datei oder HTTP)

Der Vertrag, der bei euch schon existiert: **`kosmovis.render-scene/v1`**. Wir lesen ihn
wörtlich nach eurem Schema, nicht nach einer Beschreibung davon. Was wir daraus nehmen:

| Euer Feld | Was wir damit tun |
|---|---|
| `geometry.path` | **Pflicht.** Ohne sie gibt es nichts zu rendern. |
| `geometry.format` | Wir verarbeiten `glb`, `gltf`, `ifc`. `fbx` und `blend` weisen wir ab — mit Begründung, nicht mit einem Absturz zwei Stufen später. |
| `cameras` | Liste von `CameraSpec` (`name`, `position`, `target`, `fov`) **oder** `"auto"`. Bei `"auto"` leiten wir zwölf Standpunkte aus der Bounding Box ab. `"saved"` weisen wir ab — wir haben keinen Zugriff auf eure gespeicherten Kameras und würden sonst stillschweigend andere Blickwinkel rendern als bestellt. |
| `render.resolution` | Paar `[Breite, Höhe]`. |
| `render.samples` | Cycles-Samples für die Geometriestufe. |
| `render.faithful` | Geht auf unsere `controlnet_staerke`. **Siehe Vorbehalt unten.** |
| `render.sun` | Wird zurzeit **nicht** bedient — unser Runner setzt eine feste Sonne. Wir melden das als Warnung, statt so zu tun als ob. |
| `style.prompt`, `style.mode`, `style.refs` | Prompt und Stilreferenzen. |
| `vis.backbone` | **Siehe Vorbehalt unten.** |
| `vis.skip`, `vis.upscale` | durchgereicht. |

Ein **`fov`** ist bei uns **horizontal** gelesen. Euer Schema sagt nicht, um welche Achse
es geht, und beide Lesarten liefern eine plausible Zahl — bei 16:9 mit fast einem Faktor
zwei Unterschied. Das ist die eine Stelle, an der wir eine Annahme treffen statt zu
messen, und sie gehört an der ersten echten Naht überprüft. **Bitte bestätigt oder
widersprecht sie.** Ein um den Faktor zwei falscher Bildwinkel fällt an einem einzelnen
Bild nicht auf, sondern erst, wenn jemand zwei Bilder nebeneinanderlegt.

Eure Bildwinkelgrenzen (`min 10`, `max 120`) prüfen wir **beim Senden**, nicht beim
Empfangen — ein Auftrag, den eure Warteschlange abweisen würde, soll bei uns scheitern,
wo noch jemand hinsieht.

Dasselbe für die Auftragskennung: Euer Schema verlangt `^vis-\d+-[0-9a-f]{6}$`. Wir
prüfen dagegen und **benennen nicht um**. Eine Kennung ist die Klammer zwischen Auftrag,
Bildern und Protokoll; wer sie an der Naht still ändert, macht ein Ergebnis unauffindbar.

### Weg B — Die Werkzeugnaht (MCP)

Wenn eure Knoten Werkzeuge aufrufen statt Dateien zu schreiben, bieten wir drei an:

- **`aiimaging_enqueue_render`** — legt einen Auftrag an. Nimmt `ifc_path` **oder**
  `glb_path`, dazu `up_axis`, `bbox`, `out_dir`, `aufloesung`, `samples`,
  `approval_token`.
- **`aiimaging_query_render`** — fragt Zustand und Ergebnis ab.
- **`aiimaging_check_geometry`** — prüft Massstab und Georeferenz, **ohne** die GPU
  anzurühren.

Zwei Eigenschaften, die ihr kennen solltet, weil sie eure Knotenlogik betreffen:

- `enqueue` **führt nichts aus.** Es antwortet mit `awaiting_approval` oder `queued`,
  nie mit `running`. Ohne `approval_token` (`CONFIRMED_RENDER_…`) bleibt der Auftrag
  liegen und rührt die GPU nicht an. Das ist kein Versehen, sondern der Schutz davor,
  dass ein Klick eine Stunde Rechenzeit auslöst.
- `job_id` und `status` sind **nullbar**. Ein Auftrag, der gar nicht erst angelegt wurde
  — abgelehnt vom Torwächter, fehlende Geometriequelle — hat weder Kennung noch Zustand.
  Dann steht der Grund in `error`. Wer `job_id` als nicht-nullbar verdrahtet, sieht statt
  der Ursache einen Schemafehler.

### Was wir *nicht* von euch brauchen

Keine laufende Blender-Oberfläche, kein Add-on, kein `bpy` in eurem Prozess. Blender
läuft bei uns als **Subprozess** (`blender --background --python …`). Das ist eine
Lizenzentscheidung und nicht verhandelbar: Blender ist GPL, die saubere Grenze ist der
Prozessaufruf.

Und keine echten Projektdaten für den Aufbau der Naht — Testgeometrie erzeugen wir
synthetisch.

---

## 2 · Was ihr zurückbekommt

**`kosmovis.render-result/v2`**, euer Vertrag, wörtlich bedient:

```json
{
  "schema": "kosmovis.render-result/v2",
  "job_id":  "vis-1755600000-a1b2c3",
  "images":  ["…/vis_nord.png", "…/vis_suedost.png"],
  "qa": {
    "geometry": { "geometry_fidelity": 0.71, "spearman": -0.86, "geom_iou": 0.59,
                  "threshold": 0.65, "passed": true,  "method": "…" },
    "style":    { "style_score": 0.69, "threshold": 0.666, "passed": true,
                  "method": "siglip2" },
    "verdict":  { "passed": true, "reason": "Geometrie 0.71 gegen 0.65; Stil 0.69 gegen 0.666 (siglip2)" }
  },
  "timings": { "…": 12.4 }
}
```

Wer strikt gegen euer Schema prüft, nimmt unsere Fassung ohne Zusatzfelder; wer die
Begründungen mitlesen will, das volle Wörterbuch. Beides ist eine Funktion, kein
Handbetrieb.

### Drei Stellen, an denen wir eurem Vertrag *nicht* folgen

Das ist der ehrliche Teil dieses Blatts. Euer Vertrag ist gut gebaut, aber an drei
Stellen schreibt er Vorgabewerte fest, von denen wir inzwischen **gemessen** haben, dass
sie nicht stimmen. Sie stillschweigend zu bedienen hiesse, einen bekannten Fehler in eure
Oberfläche zu tragen, wo ihn niemand mehr findet.

**a) Die Stil-Schwelle `0.30` und das Verfahren `'dinov3'`.**
Wir haben am 18.08.2026 an **4950 Bildpaaren** gemessen: Der Boden von SigLIP 2 liegt bei
**0.526**. Gegen eine Schwelle von 0.30 besteht damit **jedes beliebige Bildpaar** — ein
Foto einer Kaffeetasse gegen euren Referenz-Render besteht. Ein Abzeichen „Stil
bestanden" gegen 0.30 sagt buchstäblich nichts aus.

Wir senden darum **immer** unsere Schwelle (`0.666`, aus dem gemessenen Boden abgeleitet)
und unser Verfahren mit. Euer Schema lässt gesendete Felder jeden Vorgabewert schlagen —
technisch ändert sich für euch also nichts, ausser dass das Abzeichen etwas bedeutet.
**Bitte zeigt `threshold` und `method` neben dem Abzeichen an**, nicht nur das grüne
Häkchen. Wer ein rotes Abzeichen sieht, soll nicht bei uns nachfragen müssen, wogegen
geprüft wurde; darum steht es zusätzlich als Satz in `verdict.reason`.

**b) `vis.backbone` kennt unser Modell nicht.**
Eure Liste führt `qwen`, `flux2-klein`, `flux-krea`, `sdxl`. Unser Vorgabemodell
**`z-image-turbo`** steht nicht darin. Wir **raten nicht** und fallen **nicht** auf eure
Vorgabe zurück — ein stillschweigend ersetztes Modell wäre ein anderes Bild unter
demselben Auftrag. Wir melden die Lücke.

Warum das nicht nur Formsache ist: Der bei euch vorgegebene `qwen` **verliert die
Geometrie**, wo `z-image-turbo` sie hält (Spearman +0.005 gegen −0.853, am Gerät gemessen
in `auf-20260818-13`). Wenn euer Auftrag `qwen` sagt, rendern wir `qwen` — aber die
Geometrie-QA wird es rot melden, und das ist dann kein Fehler unserer Kette.

Von euren vier Einträgen ist unter unserer Lizenzregel genau **einer** ausgeschlossen:
`flux-krea` (FLUX-Ableger, nicht-kommerziell). `flux2-klein` ist Apache-2.0 und
zulässig — das hatten wir zwischenzeitlich falsch notiert und korrigiert.

**c) `faithful` ist ein einzelner Regler von 0 bis 1.**
Bei uns hängt „wie treu" an mindestens drei Grössen, und die Wirkung ist **nicht
monoton**: gemessen schneidet 0.80 besser ab als 1.00. Wir reichen den Wert an
`controlnet_staerke` durch, weil das die einzige ehrliche Zuordnung ist, und vermerken
in den Hinweisen, was dabei unter den Tisch fällt. Wenn ihr den Regler beschriftet:
**„höher" ist nicht „besser".**

### Und eine Stelle, an der wir eine Entscheidung von euch brauchen

Die HTTP-Brücke erzeugt den Freigabe-Token (`CONFIRMED_RENDER_…`) **selbst**, mit
`secrets.token_hex`. Ein selbst geprägter Token belegt keine menschliche Freigabe. Wir
lesen ihn deshalb standardmässig **nicht** als Freigabe — der Auftrag bleibt liegen.

Das ist eine Betreiberentscheidung und keine Programmentscheidung; sie ist als Schalter
gebaut, nicht als Verhalten. **Wenn bei euch ein Mensch vor dem Absenden bestätigt, sagt
uns wo**, dann schalten wir um.

---

## 3 · Woran ihr erkennt, dass eine Verbindung wirklich trägt

**Das ist die eigentliche Übergabe.**

Der Anlass ist konkret: In der vorgeführten Oberfläche meldet der Knopf **Ausführen** den
Zustand `bereit` — und tut nichts. Das ist genau der Befund, mit dem dieses ganze Projekt
angefangen hat, nur an anderer Stelle: **Ein Zustand, der „bereit" behauptet, ohne die
Verdrahtung geprüft zu haben.**

Eine Kante zwischen zwei Knoten kann existieren und trotzdem nichts tragen. Der Vorgänger
liefert `depth_png`, der Nachfolger erwartet `depth_map` — die Kante ist gezeichnet, der
Graph sieht vollständig aus, und der Fehler erscheint erst nach der teuersten Stufe. Bei
uns hiess der Merksatz dazu, teuer bezahlt:

> **Die Existenz einer Datei ist kein Beleg für ihren Inhalt — und ihr Fehlen keiner für
> ihre Abwesenheit.**

Für Kanten gilt dasselbe. Darum haben wir zwei Prüfungen gebaut, die **vor** dem Rechnen
laufen und deren Antwort ihr direkt an euren Knopf hängen könnt:

### `pruefe_verdrahtbarkeit(erzeuger, verbraucher)` — für die äussere Naht

Nimmt zwei Werkzeugverträge und sagt, ob die Ausgabe des einen die Eingabe des anderen
wirklich deckt. Feldweise, nicht „beide sind verbunden".

### `pruefe_kette(graph)` / `pruefe_bedarf(graph, bedarf)` — für den inneren Graphen

Prüft einen Graphen **ohne ihn auszuführen**. Beide geben dieselbe Gestalt zurück, damit
beide Ebenen gleich gelesen werden:

```python
[{"knoten": "qa", "art": "qa", "befund": "fehlender-eingang",
  "schwere": "error", "detail": "…"}]
```

**Leer heisst verdrahtet.** Vier Befundarten:

- **`fehlender-eingang`** — der Knoten erwartet einen Slot, den es nicht gibt. Der
  klassische Fall: eine QA mit nur einem Vorgänger. Sie hätte kein Ist zum Vergleichen.
- **`fehlendes-feld`** — die Kante existiert, aber der Vorgänger sagt das erwartete Feld
  nicht zu. **Das ist die tote Kante.** Genau der Fall, den ein Knopf mit `bereit` nicht
  sieht.
- **`unbenutzter-eingang`** — nur `warn`: Eine Kante darf auch bloss eine Reihenfolge
  erzwingen.
- **`unbekannte-art`** — für diese Art ist nichts deklariert, also ist an ihr nichts
  prüfbar. Wird **gemeldet** statt stillschweigend für richtig gehalten. Das ist der
  Unterschied zwischen „geprüft und in Ordnung" und „nicht geprüft".

Der Graph wird dafür **nicht** topologisch sortiert — auch ein Graph mit Kreis soll sich
prüfen lassen, sonst verdeckt der eine Fehler den anderen. Die Ausgabe ist nach Knoten-ID
sortiert und zwischen zwei Läufen gleich.

### Was wir euch damit vorschlagen

**Der Knopf soll nicht `bereit` sagen. Er soll sagen, was fehlt.**

Drei Zustände statt zwei:

| | |
|---|---|
| **verdrahtet** | Die Prüfung ist leer. Ausführen ist sinnvoll. |
| **trägt nicht** | Mindestens ein `error`-Befund. Ausführen wäre verschwendete Rechenzeit — und zwar Stunden. Zeigt den `detail`-Satz, er ist dafür geschrieben. |
| **ungeprüft** | Eine Art ohne Deklaration, oder die Prüfung ist gar nicht gelaufen. **Das ist nicht dasselbe wie „in Ordnung".** |

Der dritte Zustand ist der wichtige. `passed: false` in unserem Ergebnis heisst aus
demselben Grund **nicht** „durchgefallen", sondern „ungeprüft", wenn gar keine QA lief —
und `verdict.reason` sagt das dann wörtlich. Ein Abzeichen, das nicht zwischen
*bestanden*, *durchgefallen* und *nicht gemessen* unterscheidet, ist kein Abzeichen.

---

## Was wir zusätzlich anbieten, wenn ihr es wollt

Nichts davon ist Voraussetzung für die Naht. Es liegt fertig da und ist aus Python heraus
ohne Oberfläche aufrufbar:

- **Kamerastandpunkte** aus der Bounding Box: zwölf benannte Richtungen, Augenhöhe über
  Terrain, Zielpunkt garantiert innerhalb des Gebäudes, und die Angabe, wie weit
  zurückgetreten werden muss, damit nichts abgeschnitten wird. Wenn euer
  **Auto-Kamera**-Knoten `Eingang` / `Übersicht` / `Innenraum` anbietet, ist das die
  Schicht darunter.
- **Prompt-Bausteine** in sieben Kategorien (Komposition, Tageslicht, Himmel, Atmosphäre,
  Materialdetail, Vegetation, Personen) und sieben Stile. Dazu ein **Bauteilwächter**,
  der meldet — nicht verbietet —, wenn ein Prompt Bauteile beschreibt, die die Geometrie
  bestimmen soll und nicht der Text.
- **Geometrie-QA** mit einem Wert, der aus zwei unabhängigen Messungen zusammengesetzt
  ist, statt aus einem Gefühl.

Wenn ihr davon etwas braucht, sagt welches — dann bauen wir die Naht dorthin. Was wir
**nicht** tun, ist eure Oberfläche zu erraten und dafür zu bauen.

---

## Was wir von euch brauchen, in einer Liste

1. **Ist `fov` horizontal oder vertikal?** Einzige Annahme in diesem Blatt.
2. **Bestätigt oder widersprecht die Stil-Schwelle.** Wir senden `0.666` statt eurer
   `0.30`, mit Begründung oben.
3. **Wo bestätigt bei euch ein Mensch?** Davon hängt ab, ob wir den Freigabe-Token der
   Brücke gelten lassen.
4. **Welchen Weg wollt ihr** — Szenenvertrag oder Werkzeugnaht? Beide sind gebaut; wir
   fragen nur, damit wir wissen, welcher zuerst gehärtet wird.
5. **Soll euer Ausführen-Knopf prüfen?** Wenn ja, ist die Prüfung da und braucht nur
   angeschlossen zu werden.

Solange diese Antworten fehlen, bauen wir **nichts, was an einer bestimmten Oberfläche
hängt** — und arbeiten weiter an Verträgen, QA und Bildkette. Das trägt in jedem Fall.
