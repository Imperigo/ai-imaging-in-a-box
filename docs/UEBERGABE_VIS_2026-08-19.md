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

Drei Fragen, und sie sind der Kern:

1. **Was schicke ich euch?**
2. **Was bekomme ich zurück?**
3. **Woran erkenne ich, dass eine Verbindung wirklich trägt?**

Die dritte ist die wichtigste. Dazu ein viertes Kapitel, das nicht die Naht betrifft,
sondern **drei Dinge auf eurer Seite**, die uns beim Messen aufgefallen sind. Sie stehen
hier, weil sie euch gehören und weil wir sie nicht stillschweigend umgehen wollen — eines
davon betrifft eure Grafikkarte.

---

## 0 · Die Naht ist keine Absicht mehr — sie liegt

Zwischen dem ersten Entwurf dieses Blatts und seiner zweiten Fassung ist jemand bei uns
den ganzen Weg als Nutzer durchgegangen, mit Maus und Tastatur. Das Ergebnis ändert die
Tonlage dieses Dokuments:

**Eure Kette trägt bis in die Bridge.** Oberfläche → Graph → Knoten → Kanten → Prompt →
Geometrie-Export → Kamerasetzung → Auftrag in der Warteschlange. Was dort liegt:

```
vis-1787123048-098c6e/
  job.json            status queued · approval_token CONFIRMED_RENDER_… ·
                      idle_window_only true · engine cycles · style lineart
  model.glb           110 KB — echte Geometrie, exportiert und übertragen
  render-scene.json   schema kosmovis.render-scene/v1 · drei aus dem Modell
                      gerechnete Kameras
```

**Das ist Wort für Wort das Verzeichnis, das `bruecke.py` liest.** Der Ordnername passt
auf unser Muster, die Auftragskennung auf eure eigene Form, das Schema ist das, gegen das
wir übersetzen. Wir haben das gegen die echten Werte geprüft, nicht angenommen.

**Und der Auftrag wird nicht abgeholt.** Er stand auf *„wartet auf GPU-Leerlauf"*, auch
nachdem die Karte frei war.

*Nachgemessen am 20.08.2026, und die Antwort ist einfacher als die Vermutungen:* Es liegt
weder an einer trägen Erkennung noch an einer zu engen Schranke. **Es läuft schlicht kein
Abholer** — Einzelheiten in Kapitel 4.1. Die Stelle ist damit eindeutig:

> **Genau da hört eure Seite auf, und genau da fängt unsere an.** Was fehlt, ist der, der
> das Verzeichnis abholt, rendert, prüft und `render-result.json` danebenlegt.

**Nachtrag vom 20.08.2026: Den gibt es jetzt.** `abholer.py` liest ein Auftragsverzeichnis
eurer Warteschlange, schickt es je Kamera durch Multipass, Render und Geometrie-QA und legt
`render-result.json` nach eurem Vertrag daneben. Der echte Auftrag mit seinen drei Kameras
(Eingang, Übersicht, Innenraum) ergibt drei Bilder und drei Urteile.

Fünf Entscheidungen fallen dabei, und ihr solltet sie kennen, weil sie euer Verhalten
betreffen:

- **Ohne menschliche Freigabe wird nicht gerechnet** — der Auftrag geht dann nicht einmal
  auf `running`, damit er nicht aussieht, als arbeite jemand daran. Siehe die
  Token-Frage unten.
- **`idle_window_only` wird eingehalten, und zwar fail-closed:** Ohne Auskunft über die
  Grafikkarte wird *nicht* gerechnet. Ungeprüft ist nicht dasselbe wie frei.
- **Erst das Ergebnis, dann der Laufzettel** — sonst gibt es ein Zeitfenster, in dem eure
  Oberfläche ein Ergebnis sucht, das noch nicht da ist.
- **Ein Fehler ist ein Ergebnis:** Scheitert etwas, steht der Auftrag auf `error` **mit
  Begründung**, nie einfach still. Ein Auftrag ohne Antwort ist für den Wartenden dasselbe
  wie ein hängender Rechner.
- **Verwaiste Aufträge werden gemeldet, nicht wiederbelebt.** Steht einer auf `running`,
  weil unser Rechner mitten im Lauf ausging, reihen wir ihn **nicht** automatisch neu ein —
  ein zweiter Lauf kostet eine GPU-Stunde und kann ein zweites Bild unter derselben
  Kennung erzeugen.

Was noch **nicht** läuft: die Stil-QA. Sie braucht ein Referenzset, das uns gehört; die
bisherigen Referenzen sind fremde Bildschirmfotos. Das Ergebnis sagt dann ausdrücklich
*ungeprüft* und nicht *durchgefallen*.

Zwei Dinge fallen dabei erfreulich zusammen: Euer `idle_window_only: true` ist bei uns
`nur_bei_leerlauf` und eine **fail-closed** Schranke — bei unbekanntem GPU-Zustand wird
nicht gerechnet. Und euer `approval_token` heisst genau wie unserer. Über den zweiten
Punkt müssen wir allerdings reden, siehe unten.

Drei Zahlen, die auseinanderlaufen und die ihr kennen solltet, bevor jemand Bilder
vergleicht:

- **Augenhöhe.** Eure Auto-Kamera setzt `Eingang` auf **1.30 m** und `Innenraum` auf
  **1.60 m**. Wir rechnen mit **1.70 m über Terrain** (`AUGENHOEHE_M`), und das
  Pflichtenheft verlangt dasselbe. Kein Fehler eurer Kette — aber zwei Bilder derselben
  Szene sehen dadurch verschieden aus, und niemand wüsste warum.
- **`engine: cycles`** und **`style: lineart`** stehen im Laufzettel, nicht im
  Szenenvertrag. Wir reichen den Laufzettel unverändert durch, lesen diese Felder aber
  **nicht** — sagt uns, ob sie verbindlich sein sollen.
- **`Übersicht` auf 38.04 m** ist eine Vogelperspektive. Unsere zwölf abgeleiteten
  Standpunkte stehen auf Augenhöhe; die Übersicht ist bei uns ein eigener Fall. Kein
  Widerspruch, nur eine andere Voreinstellung.

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

### Und eine Warnung zu unserer eigenen Zahl, bevor ihr sie anzeigt

Wir sagen euch weiter unten, warum eure Stil-Schwelle von 0.30 nichts taugt. Es wäre
unredlich, dabei zu verschweigen, was wir am 20.08.2026 über **unsere eigene**
Geometrie-Schwelle gemessen haben.

> **`geometry_fidelity` mit `threshold: 0.65` ist noch kein tragfähiges Gate.**

Gemessen an vier Kontrollbildern, die *nicht* aus dem Bildmodell stammen, auf derselben
Soll-Karte und durch dieselbe Kette:

| Kontrollbild | Score | Gate 0.65 |
|---|---|---|
| gerenderte Geometrie (perfekt) | 0.984 | ✓ |
| **weisses Rauschen** | **0.722** | **✓** |
| leeres Graubild | 0.519 | ✗ |

**Weisses Rauschen besteht das Gate.** Der Grund liegt nicht am Rauschen: Unser
Tiefenschätzer legt in *jedes* Bild eine zum Horizont laufende Bodenebene, und eine Szene,
die zu 60 % aus Boden besteht, *ist* im Wesentlichen so eine Rampe. Die Rangkorrelation
misst dann zwei Bodenrampen gegeneinander.

In der Gegenrichtung dasselbe Problem: Bei einer freigestellten Szene mit wenig Grund
(17 % der Bildfläche) deckelt die Überdeckung so tief, dass **selbst ein perfektes Bild**
nur 0.64 erreicht — die Schwelle ist dort **unerreichbar**.

**Was das für euch heisst, konkret:**

* **Zeigt das Abzeichen nicht als „bestanden/durchgefallen" allein.** `threshold` und
  `method` stehen ohnehin im Ergebnis; bis diese Zange gelöst ist, ist der Zahlenwert
  aussagekräftiger als das Häkchen.
* **Ein grünes Geometrie-Abzeichen ist zurzeit kein Beleg für Geometrietreue.** Wir sagen
  euch das jetzt, statt es in sechs Monaten zu berichtigen.
* Wir liefern den Wert weiter — er ist nicht wertlos, er ist **noch nicht kalibriert**.
  Woran wir arbeiten, steht unten unter „Was wir zusätzlich anbieten".

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

*Am lebenden Auftrag bestätigt:* Der Laufzettel in `vis-1787123048-098c6e` trägt
`approval_token: CONFIRMED_RENDER_…` neben `idle_window_only: true`. Der Mensch hat dort
auf **Ausführen** gedrückt — das ist eine Handlung, und sie könnte als Freigabe zählen.
Aber der Token belegt sie nicht, denn er entsteht unabhängig davon im Code. **Genau darum
fragen wir**, statt es zu entscheiden: Der Unterschied zwischen „ein Mensch hat gedrückt"
und „ein Token liegt vor" kostet im schlechten Fall eine Stunde GPU-Zeit, die niemand
bestellt hat.

*Und die Frage ist inzwischen dringender als beim ersten Entwurf:* Solange **niemand**
abholt, richtet ein grosszügig gelesener Token keinen Schaden an. Sobald ein Abholer
läuft — unserer oder eurer —, entscheidet diese eine Einstellung darüber, ob ein Klick
eine GPU-Stunde auslöst. Siehe auch 4.2: Eure vorhandene Worker-Komponente liest die
Auflage **gar nicht**.

---

## 3 · Woran ihr erkennt, dass eine Verbindung wirklich trägt

**Das ist die eigentliche Übergabe.**

Der Anlass ist konkret, und er ist inzwischen **gemessen statt vermutet**: Der Zustand
eures Render-Panels meldet `bereit` **auch bei unverdrahteten Knoten**.

*Berichtigung an uns selbst, noch am selben Tag:* Wir hatten zuerst notiert, der Knopf
„sagt nicht, warum er schweigt". **Das war falsch.** Er sagt es sehr genau — die Meldung
(*„kein Prompt — verbinde Stimmung/Stil oder fülle das Formular"*) war von der
Node-Palette **verdeckt**. Eure Fehlermeldungen sind gut; eine davon trennt sogar
sauber **Erreichbarkeit von Berechtigung** (*„Die Bridge antwortet — der Render-Ruf wurde
trotzdem abgewiesen, wahrscheinlich fehlt der Token"*), und sie stimmte aufs Wort:
`/health` → 200, geschützte Route → 401. Das ist besser als das meiste, was wir an
Fehlermeldungen kennen.

**Der eine echte Mangel an dieser Stelle ist also nicht das Schweigen, sondern der
Zustand:** `bereit` steht dort, bevor irgendeine Kante gezogen ist. Und das ist genau der
Befund, mit dem dieses ganze Projekt angefangen hat, nur an anderer Stelle: **ein
Zustand, der Bereitschaft behauptet, ohne sie geprüft zu haben.**

*Zweite Berichtigung, und sie schränkt uns ein:* Wir hatten zusätzlich notiert, ein Druck
im unverdrahteten Zustand bleibe **wirkungslos**. Das gilt nicht mehr. Nachgemessen mit
`document.elementFromPoint` an genau der Klickkoordinate: Der Vergrössern-Knopf (44 × 44
bei 895,741) überdeckt die obere linke Ecke des Ausführen-Knopfs (84 × 32 bei 911,759),
und der Klick lag darin. **Er hat den Ausführen-Knopf nie erreicht.**

Was steht: Das Panel **zeigt** `bereit` bei unverdrahteten Knoten — das ist eine Ablesung
und kein Klick. Was **ungemessen** ist: ob dieser Zustand auch lügt, wenn man ihn drückt.

Zwei Dinge nehmen wir daraus mit. Erstens gehört die Überdeckung selbst gemeldet: Ein
44-Pixel-Knopf, der die Ecke des Hauptknopfs verdeckt, trifft nicht nur uns. Euer eigener
Insel-Überdeckungs-Wächter hat dieselbe Stelle unabhängig gefunden — Station `vis`,
Zustand `popup:render-senden`, bei 1400 × 900. Zweitens: *Aus einem ausbleibenden Effekt
auf eine Ursache zu schliessen, ohne zu prüfen, ob die Handlung überhaupt ankam*, ist
derselbe Fehler wie überall sonst in diesem Blatt — nur diesmal unserer.

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

## 4 · Drei Dinge auf eurer Seite, die ihr wissen solltet

Wir haben am 19. und 20.08. an eurer Maschine gemessen — mit Erlaubnis und ohne etwas zu
ändern. Dabei sind drei Dinge aufgefallen, die **nicht** unsere Naht betreffen, sondern
eure Komponenten. Sie stehen hier, weil sie euch gehören und weil wir sie nicht
stillschweigend umgehen wollen.

### 4.1 · Der Auftrag bleibt liegen, weil **niemand ihn abholt**

Nicht: „die Erkennung ist träge". Nicht: „die Schranke ist zu eng". Sondern:

> Es läuft **kein Abholer**. Kein `blender_worker`-Prozess, kein ComfyUI-Worker, kein
> Dienst — nur die Bridge selbst. Und keine Schranke stand im Weg: **0 % Auslastung gegen
> eine Schwelle von 10 %.** Der Auftrag lag seit 09:04 unberührt.

Das ist eine gute Nachricht, denn es ist die Sorte Lücke, die man füllen kann. **Wir haben
den Abholer** — Kapitel 0 beschreibt ihn, und er liest euer Verzeichnisformat, wie es ist.

### 4.2 · Euer `blender_worker` hat **kein Leerlauf-Tor** — und das ist der unangenehme

Die Komponente existiert, sie läuft nur gerade nicht. Beim Nachsehen fiel auf:

> Sie prüft **nirgends**, ob die Grafikkarte frei ist. Wer sie startet, umgeht
> `idle_window_only` — **unbemerkt.** Der Auftrag trägt die Auflage, und niemand liest sie.

Das ist genau die Fehlerart, die uns in Sitzung 07 vier Löcher gekostet hat: eine Zusage,
die im Dokument steht und im Code nicht. Bei uns ist die Prüfung darum **fail-closed** —
ohne Auskunft über die Karte wird nicht gerechnet, weil *ungeprüft* nicht *frei* heisst.

**Wir melden das und tun nichts daran.** Es ist eure Komponente und eure Grafikkarte. Aber
wer den Worker in Betrieb nimmt, sollte es vorher wissen — sonst belegt der erste Auftrag
mit `idle_window_only` die Karte mitten in einer Vorführung.

### 4.3 · Die Kamerahöhe steht zweimal im Code, mit **zwei verschiedenen Bezugspunkten**

Beide Male 1600 mm — einmal gerechnet ab dem **Hüllbox-Minimum**, einmal ab der
**Geschosshöhe**. Wir und das Pflichtenheft rechnen mit **1700 mm über Terrain**.

Das sind zwei Zahlen und **drei Bezugspunkte** für dieselbe Grösse — und der gefährliche
Teil ist nicht die Differenz von 100 mm, sondern der Bezugspunkt: Bei einem Gebäude mit
Untergeschoss liegt das Hüllbox-Minimum **im Erdreich**, und eine Kamera 1,6 m darüber
steht im Keller. Der Fehler ist dann nicht klein, sondern ein ganzes Geschoss gross, und
er sieht auf dem Zahlenweg nach nichts aus.

Bei uns hat genau das drei Fehler erzeugt, die **kein einziger Test gefunden hat** — sie
fielen erst auf, als jemand zwölf gerenderte Bilder ansah. Wir führen die Augenhöhe
seitdem ausdrücklich als *über Terrain* mit einem eigenen Parameter `gelaende_z`, weil die
Bodenhöhe eine Angabe der Szene ist und keine Annahme des Renderers.

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
  ist, statt aus einem Gefühl — **mit dem Vorbehalt aus Kapitel 2**: Die Schwelle 0.65 ist
  noch nicht kalibriert, und wir sagen das dazu, statt es zu verschweigen.
  Was daran gerade gebaut wird: eine **Nullprobe** als fester Bestandteil des Urteils. Ein
  Score wird dann nicht mehr nur gegen eine Schwelle gehalten, sondern gegen das, was ein
  Bild *ohne jede Geometrie* auf derselben Soll-Karte erreicht. Dieselbe Medizin, die
  unsere Stil-QA seit dem 18.08. nimmt — und genau das, was eurer 0.30 fehlt.

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
   angeschlossen zu werden. Konkret: `bereit` erst, wenn `pruefe_kette` leer ist.
6. **Warum wird der Auftrag in `/tmp/kosmo-jobs/` nicht abgeholt?** Träge Erkennung oder
   zu enge Leerlauf-Schranke — bei uns ungemessen. **Das ist die Stelle, an der wir
   einsteigen können**, und die einzige Frage dieser Liste, die eine Demo aufhält.
7. **Augenhöhe 1.30/1.60 oder 1.70 m — und ab wo gemessen?** Das Pflichtenheft sagt
   1.70 m **über Terrain**. Im Code stehen zwei verschiedene Bezugspunkte, siehe 4.3. Wer
   nachgibt, ist uns gleich — aber es sollte **eine** Zahl mit **einem** Bezugspunkt sein.
8. **Sind `engine` und `style` im Laufzettel verbindlich?** Wir reichen sie durch und
   lesen sie nicht.
9. **Nehmt ihr den Abholer?** Es läuft keiner, und wir haben einen. Wenn ja, sagt uns,
   ob `fremde_freigabe_gilt` gesetzt werden soll (Frage 3) — das ist die einzige
   Einstellung, die noch fehlt.
10. **Soll euer `blender_worker` ein Leerlauf-Tor bekommen?** Wir bauen es nicht in eure
    Komponente, aber wir sagen gern, wie unseres aussieht: fail-closed, und bei unbekanntem
    Zustand wird nicht gerechnet.
11. **Welche Hochachse hat eure `model.glb`?** `render-scene/v1` hat **kein Feld dafür**.
   Wir nehmen `Y_UP` an, weil die glTF-Spezifikation es vorschreibt — aber genau hier
   liegt der Befund, mit dem dieses Projekt angefangen hat: Zwei Erzeuger eures
   Ökosystems liefern beide ein `glb_path`, mit **unterschiedlicher** Orientierung. Eine
   verdrehte Hochachse dreht Tiefenkarte, Kamera und Geometrie-QA gemeinsam und **fällt
   an einem einzelnen Bild nicht auf**. Ein Feld im Vertrag wäre uns lieber als unsere
   Annahme.
12. **Wie viele automatische Standpunkte soll `cameras: "auto"` bedeuten?** Wir rendern
    **einen**. Zwölf wären zwölf GPU-Läufe, und wie viele ein Auftrag wert ist, ist eure
    Entscheidung und nicht unsere.

Solange diese Antworten fehlen, bauen wir **nichts, was an einer bestimmten Oberfläche
hängt** — und arbeiten weiter an Verträgen, QA und Bildkette. Das trägt in jedem Fall.


13. **Nimmt euer Schema `null` für `style_score` an?** Seit dem 21.08.2026 ist unser
    Hausstil **fest formuliert** und wird gegen einen gemessenen **Belichtungsrahmen**
    geprüft (Mittel ± 2σ), nicht gegen ein Referenzset. Das beantwortet dieselbe Frage wie
    euer Feld — *sieht das aus wie gewollt?* —, aber mit einem anderen Mittel.

    Eine Belichtungsprüfung hat **keinen natürlichen Skalar.** Wir schicken darum
    `style_score: null` und `threshold: null`, und schreiben in `method`, womit geprüft
    wurde (`belichtungsrahmen/<stil>`). Eine Zahl zu erfinden — auch eine ehrlich gemeinte
    wie 1.0 für „bestanden" — sähe in eurer Oberfläche genau wie eine gemessene
    Bildähnlichkeit aus, und das wäre eine stille Falschaussage.

    **Eure Schemadatei liegt uns nicht vor**, also wissen wir nicht, ob `null` dort
    durchgeht. Wenn nicht, schlägt der Auftrag erst in eurer Warteschlange fehl — und dann
    ist das dort zu ändern und nicht bei uns durch eine erfundene Zahl. Sagt uns bitte,
    was ihr braucht: `null` zulassen, ein eigenes Feld, oder das Abzeichen weglassen,
    solange keine Ähnlichkeit gemessen wurde.