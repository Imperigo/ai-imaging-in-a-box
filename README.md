# Visbox

*Das Repo heisst `ai-imaging-in-a-box`, die Software heisst **Visbox** (Owner-Entscheid
18.09.2026). Auf PyPI: `pip install visbox`. Der Importpfad bleibt `aiimaging` — wie bei
`pip install pillow` → `import PIL`; die Begründung steht in `pyproject.toml`.*

Vertiefungsarbeit ETH Zürich · HS26 · ITA · Betreuung Gonzalo Casas

Ein lokal lauffähiges, knotenbasiertes Framework für geometrie-treue KI-Architektur-
Visualisierung: IFC-Geometrie hinein, **verifizierte** Bilder heraus — ohne Cloud, mit
austauschbarem lokalem Bildmodell.

Das Wort, auf das es ankommt, ist *verifiziert*. Ein Bildmodell erfindet gern ein
Geschoss dazu. Der Kern dieser Arbeit ist darum nicht das Erzeugen, sondern das **Messen**:
ein Verfahren, das ein erzeugtes Bild gegen die Geometrie hält, aus der es entstanden ist,
und eine erfundene Kubatur nachweislich durchfallen lässt.

---

## Stand

**Stand 2026-09-29.** Die Kette läuft von der Modelldatei bis zum bewerteten Bild — am
Gerät und auf dem Weg, den das Produkt geht: Modell öffnen, Mappe anlegen, wieder öffnen,
rechnen, Bild mit Urteil (`auf-20260922-137`). Seit dem 24.09. entsteht ein Bild auch aus
der Knotenansicht heraus, nachdem ein Mensch freigegeben hat (`auf-20260924-164`). Der
erste echte Render überhaupt war am 18.08.2026.

**Was die Prüfung heute belegt, und was nicht.** Die schlechten Nachrichten zuerst, weil
an ihnen die Arbeit hängt:

* **Auf dem Produktweg hat noch kein Bild die Geometrie-Schwelle bestanden.** Der beste
  Lauf kam auf 0,534 gegen 0,65 (`auf-20260923-154`).
* **Das gesuchte Bild existiert — aber an einer einfachen Schachtel.** Am 09.09. bestanden
  zwölf von zwölf Bildern (`auf-20260909-92`). An einem gegliederten Bau misst dieselbe
  Zahl schon bei richtiger Zuordnung nur 0,36. Es liegt an der Szene, nicht am Messweg
  (`auf-20260921-128`).
* **Die zusammengesetzte Zahl allein belegt wenig.** Sie besteht auch gegen die
  Tiefenkarte eines fremden Gebäudes, weil sie zum grossen Teil den Aufbau Boden–Himmel
  misst. Was trennt, ist **`rho_maske`**: wie gut die Tiefe des Bildes zur Geometrie passt,
  gemessen nur auf dem Gebäude.
* **Seit dem 29.09. urteilt über ein Bildpaar nur noch diese eine Zahl.** Das zweite Bein
  (die Kante am Gebäudeumriss) hat an echten Bildern gewürfelt; es wird weiter angezeigt,
  entscheidet aber nicht mehr mit. **Die Schwelle 0,80 ist nicht geeicht** — die Messung
  liegt bei der HomeStation (`auf-20260929-175`).
* **Ein Versuch, saubere Bilder anders zu messen, ist verworfen** (24.09.): Die «Ordnung an
  Tiefensprüngen» stellte an echten Bildern das schlechte Bild über alle guten
  (`auf-20260924-172`).

> **Das Messen ist gebaut und am Gerät gelaufen. Ein Bild, das auf dem Produktweg besteht,
> gibt es noch nicht — und die Zahl, die jetzt allein urteilt, hat noch keine geeichte
> Grenze.**

**Die Bildmodelle.** Regel 1 entscheidet, was ins Produkt darf:

| Modell | Lizenz | Rolle |
|---|---|---|
| `z-image-turbo` | Apache-2.0 | **Vorgabe** — seit dem 29.09. auch für Aufträge aus KosmoOrbit ohne Modellangabe, wie es deren Vertrag sagt. Seither das **einzige** freie Modell mit Tiefensteuerung. Knapp eine Minute je Bild |
| `qwen-image-edit-2511`, `flux2-klein-4b` | Apache-2.0 | Bearbeitungsmodelle: nehmen ein Eingangsbild, haben aber keine Tiefensteuerung. Das Qwen-Modell rechnet mit Führung durch, knapp sechs Minuten je Bild — und folgt der Geometrie gemessen nicht |
| `qwen-image-2512` | Apache-2.0 | **stillgelegt** (29.09.): 48 GB, und die Datei seiner Tiefensteuerung ist in Herkunft, Lizenz und Format ungeklärt |
| `sdxl-juggernaut`, `sd35-large` | OpenRAIL-M, Stability Community | **nur zum Messen**, nie ausgeliefert (Owner, 22.09.) — keine der Lizenzen aus Regel 1 |
| `qwen-image-2.1` | Qwen Research License | **nur Forschung** (Owner, 29.09.): lädt nur an der HomeStation und nur mit `AIIMAGING_FORSCHUNGSMODELLE=1`; nie Vorgabe, von KosmoOrbit nicht bestellbar, jeder Lauf trägt «nur Forschung». Ob es läuft und die Geometrie trägt, misst `auf-20260929-178` |
| FLUX.1-dev, FLUX.2-dev | Non-Commercial | ausgeschlossen |

**Die Naht zu KosmoOrbit:**

* **Die Post kommt jetzt an.** Seit dem 29.09. gehen Antworten und Aufträge direkt in den
  Eingangsordner von KosmoOrbit. Vorher lagen sie fünf Tage nur bei uns — zugestellt war
  nichts. Alle sechs offenen Fragen an den Cloud-Worker sind seither beantwortet.
* **KosmoOrbit hat v0.1.5 am 25.09. ohne das erste echte Bild geschnitten.** Es ist auf
  v0.1.6 verschoben. Das Urteil am Render-Knoten ist drüben entschieden, aber nicht gebaut.
* **Drüben entschieden (29.09.):** E123 — wer Daten empfängt, nimmt ein leeres Feld an und
  meldet es als Mangel. E124 — Zusatzbilder («Ebenen») kommen in zwei Schritten.
* **Bei uns dafür gebaut:** Schritt 1 der Ebenen (Schönbild, Tiefe, Material-ID je Kamera,
  mit Erklärung in Zahlen); die Felder, die sagen, mit welchem Modell gerechnet wurde
  (`engine_used`, `engine_license`, `guidance_applied`); und der Prüfblock
  `geometry_gates` in **ihren** drei Wörtern (`measured`, `not_measured`,
  `not_applicable` — das dritte als unser Vorschlag, zur Bestätigung gestellt). Dazu
  Beispieldateien mit echtem Blender unter
  [`docs/vertragsbeispiele/2026-09-29/`](docs/vertragsbeispiele/2026-09-29/) — das KI-Bild
  und die Prüfung darin sind Platzhalter, und so benannt.
* **Ein Fehler bei uns, gefunden, weil sie nachgefragt haben:** Unsere Transparenz-Prüfung
  sah Glas mit Durchlass nicht, sie kannte nur den älteren Weg. Behoben.
* **Noch nicht gebaut, bei uns:** Nach E123 sind wir an der MCP-Kante der Empfänger; vier
  Felder unseres Eingangs nehmen ein leeres Feld noch nicht an.
* **Die Token-Prüfung am Freigabe-Tor bleibt aus — als Entscheid** (29.09.): KosmoOrbit
  benutzt das Tor nicht, unser eigener Weg gibt per Knopf frei.

**Offen, und bei wem:**

* **local (HomeStation), sechs Aufträge, 173–178:** Zwillinge und Speichergrenze je Modell
  (173), zwei Nachproben zum Einbau-Stand (174), die Eichung der Paarschwelle (175), ein
  ganz echter Lauf für die Vertragsbeispiele (176), drei neue Blender-Knoten von
  KosmoPrepare (177), Qwen-Image-2.1 unter der Forschungs-Ausnahme (178).
* **cloud (KosmoOrbit):** Ebenen, Glas-Ausgabe und die neuen Vertragsfelder einbauen;
  bestätigen, dass `not_applicable` so gemeint ist.
* **Owner:** die App auf dem iPad ausprobieren — das Abnahmeblatt steht in
  [`docs/VISBOX_IPAD_ERSTE_PROBE.md`](docs/VISBOX_IPAD_ERSTE_PROBE.md).

**Was hier messbar ist:** Dieses Environment hat keine Grafikkarte, aber Blender und
`.venv-ifc` — also die **ganze Geometrieseite** mit echtem Blender. Alles, was `torch`
braucht (Bildmodell, Tiefenschätzer und damit die Geometrie-Zahl selbst), läuft nur auf
der HomeStation und geht dorthin als Auftrag.

| | Stand |
|---|---|
| Oberfläche (`oberflaeche/`) | gebaut am 21.09. **Ausserhalb des Kerns** (Regel 4), ohne fremdes Paket; von sich aus nur auf dem eigenen Rechner, im Heimnetz nur mit Kennwort. Zeigt Modell und jedes Bild mit seinem Urteil — *ein ungeprüftes Bild sieht weder aus wie ein bestandenes noch wie gar nichts*. Der Knotenbaum ist bedienbar: Einstellungen je Knoten, die Felder kommen aus der Bibliothek |
| iPad-App «Visbox» (`ipad/`) | gebaut am 22. und 23.09.: mit dem Stift ins Bild zeichnen, mit einer sechsstelligen Zahl an die HomeStation koppeln, dort rechnen lassen. Übersetzt auf einem Mac ohne Warnung. **Auf einem iPad ist sie noch nie gelaufen** — das Abnahmeblatt liegt beim Owner |
| Knotenansicht aus KosmoOrbit (`kosmovis/`) | übernommen am 24.09. (E26): das Vis-Werkzeug **wörtlich kopiert**, 198 Dateien mit Abdruck in `kosmovis/HERKUNFT.json`, 19 Stellvertreter für alles ausserhalb; 722 Proben des Originals grün. Angeschlossen an Mappe und Server. **Das erste Bild auf diesem Weg ist am 24.09. entstanden** (`auf-164`). Die Knoten-Oberfläche baut der UI-Worker in KosmoOrbit um; Visbox übernimmt sie, wenn er fertig meldet (E27) |
| Arbeitsgang — Modell herein, Kette fahren, Urteil in die Mappe | gebaut am 21.09. **Erster Aufrufer des Graphen im Produktcode.** Ein geändertes Modell hält den Lauf an; die Hochachse wird bei einer fremden glb **nicht geraten**. Am Gerät ganz durchgelaufen (`auf-137`) |
| Projekt — Modell öffnen, arbeiten, morgen weitermachen | gebaut am 21.09. Das Modell wird **verwiesen, nicht kopiert**. Zwei Geräte an derselben Mappe löschen sich nicht mehr gegenseitig die Arbeit |
| 3D-Modell-Importeur (`obj`, `fbx`, `dae`, `stl`, `ply`, `usd`, `abc`, `x3d`) | **am Gerät gemessen** (`auf-126`, Blender 5.2.1): Sechs Formate halten die Hüllbox auf den Millimeter. **Collada und X3D kann Blender 5.2 gar nicht mehr** — der Einlass sagt es dazu |
| IFC → glb, über die Prozessgrenze | läuft, an 40 echten Dateien gemessen. Der Knotenname trägt den IFC-Namen — ohne ihn war das Gelände auf der Blender-Seite nicht abtrennbar |
| glb → Blender-Multipass (Schönbild, Material-ID, Tiefe) | läuft auf Blender 4.2 **und** 5.2. Seit dem 29.09. als Ebenen je Kamera bestellbar |
| Bildmodell-Stufe (`diffusers`) | **läuft am Gerät**, Vorgabe `z-image-turbo`. Reicht der Speicher auf der Grafikkarte nicht, wartet der Auftrag mit Grund, statt abzustürzen — die Grenze gilt seit dem 24.09. je Modell, die Bestätigung steht aus (`auf-173`) |
| Geometrie-Treue-Metrik | gebaut und kalibriert — **an der Schachtel**. Am gegliederten Bau 0,36 schon bei richtiger Zuordnung (`auf-128`). Das Paarurteil hängt seit dem 29.09. an ρ allein, Grenze ungeeicht (`auf-175`) |
| Prüfungen **vor** dem Bildlauf | Rahmung, Kamerahöhe, Zwischenbilder, Doppelansicht. Seit dem 24.09. rendern alle drei automatischen Kameras auch an kleinen Bauten (`auf-169`). Die Zwillingserkennung griff im Betrieb nie — repariert, am Gerät unbestätigt (`auf-173`) |
| Stil-Gate | gebaut, Schwelle ungeprüft |
| Kette als Graph mit Zwischenspeicher | gebaut und **gemessen** (Prompt-Änderung rechnet die Geometriestufen nicht neu) — aber **nicht am Produktivweg**: der Abholer fährt die Stufen als gerade Abfolge |
| MCP-Anbindung an KosmoOrbit | registriert am 18.08., am 01.09. am Gerät mit einem echten Werkzeugaufruf nachgewiesen |
| Ein über KosmoOrbit bestellter Render | wird seit dem 26.08. ausgeführt, durch denselben Abholer und dieselben Riegel wie jeder andere. **Ein echtes Bild aus einer KosmoOrbit-Bestellung steht aus** — drüben verschoben auf v0.1.6 |
| LoRA-Stiltraining | Naht gebaut, **nie ein Training ausgeführt** |

**Wie weit der Einbau in KosmoOrbit ist**, Posten für Posten mit Datum und Beleg:
[`docs/EINBAU_STAND.md`](docs/EINBAU_STAND.md). Was Visbox heute kann, Schritt für Schritt
und für Laien: [`docs/PRODUKT_DIE_SCHRITTE.md`](docs/PRODUKT_DIE_SCHRITTE.md). Wie die
Oberfläche aussehen soll, die darüber liegt:
[`docs/OBERFLAECHE_KOSMOVIS.md`](docs/OBERFLAECHE_KOSMOVIS.md). Was uns bei der eigenen
Arbeit an der Oberfläche auffällt und an den UI-Worker geht:
[`docs/UI_BEFUNDE.md`](docs/UI_BEFUNDE.md).

Tests: **9384**, alle grün, ohne GPU. *Die Zahl steht unter einem Wächter
(`tests/test_readme.py`) — sie kann nicht mehr still veralten.*

---

## Die vier Regeln

Sie stehen vollständig in [`CLAUDE.md`](CLAUDE.md) und sind hier keine Absichtserklärung,
sondern **ausführbar** — seit dem 26.08.2026 hat jede der vier einen Wächter in der
Testsammlung. *Was nur im Text steht, veraltet, sobald jemand eine Zeile schreibt, ohne
den Text zu lesen; an einem einzigen Tag ist das achtmal passiert.*

1. **Permissive Lizenzen, kein GPL/AGPL.** `backbone.waehle(kommerziell=True)` gibt
   FLUX-dev nie zurück. `lora.pruefe_auftrag` lehnt ein Training auf einer
   Non-Commercial-Grundlage ab, bevor die erste GPU-Sekunde läuft — ein LoRA erbt die
   Lizenz seines Grundmodells. Im [`NOTICE`](NOTICE) trägt jeder Copyleft-Eintrag eine
   **erklärte** Auflösung (`AUFLOESUNG: Prozessgrenze | Lizenzausnahme | KEINE`), die ein
   Test prüft. **Seit dem 29.09.2026 gibt es eine Forschungs-Ausnahme** für ein einzelnes
   Modell (Qwen-Image-2.1): `backbone.ladefreigabe` lädt es nur mit gesetztem Schalter, nie
   als Vorgabe und nie auf Bestellung von KosmoOrbit — vor einem Verkauf wird es entfernt
   oder lizenziert.
2. **Blender nur als externer Prozess.** Kein `import bpy`, kein bpy-Wheel, kein Add-on.
   Ein Test bewacht das Produkt-Environment.
3. **Keine echten Projektdaten im Repo.** Testgeometrie wird erzeugt, nicht abgelegt.
   `auftrag.baue_ergebnis` weist eingebettete Bilddaten ab; `lora.pruefe_auftrag` weist
   einen Trainingsdatensatz *innerhalb* des Repos ab. Ein Wächter liest **jede**
   versionierte Textdatei auf Benutzernamen in Pfaden — er las bis zum 26.08. nur acht
   Dateiendungen und übersah darum drei.
4. **Der Kern ist eine Bibliothek.** Jede Fähigkeit ist aus Python heraus nutzbar, ohne
   dass eine Oberfläche läuft. Die MCP-Schicht ist ein optionaler Zusatz. Geprüft in einem
   **frischen Interpreter**: Ein Import von `aiimaging` lädt weder ein Oberflächen-Werkzeug
   noch das MCP-SDK noch `torch`.

---

## Was gemessen wurde, und was behauptet

Dieses Repo unterscheidet die beiden Dinge durchgehend — im Code, in den Dokumenten und in
den Commit-Nachrichten. Ein paar Beispiele, weil sie die Arbeitsweise besser zeigen als
eine Beschreibung:

- **Die Geometrie-Metrik ist nachweislich rangbasiert.** Eine streng monotone Umrechnung
  der Tiefe lässt den Score bei exakt 1,000. Das war die einzige Prüfung der
  Schwellenstudie, die das Verfahren hätte umwerfen können.
- **Die Schwelle 0,65 ist zu mild** — 18 von 32 gestörten Fällen gehen durch. Sie steht
  trotzdem, weil eine bessere Zahl ohne den Tiefenschätzer in der Messung nur schwächer
  unbegründet wäre. *Nicht verteidigt, sondern beibehalten.*
- **ArchiCAD über IFC4 braucht keine Einheitenumrechnung.** Die Annahme, die den Connector
  auslöste, war falsch; IfcOpenShell rechnet selbst um. Gemessen, nicht vermutet.
- **Zwei GPL-Funde** sind ausdrücklich als solche gemeldet: ComfyUI und Krita AI Diffusion.
  Beim zweiten lag die Sekundärquelle *in die gefährliche Richtung* falsch — sie meldete
  permissiv, wo Copyleft steht.

Wo etwas nicht gemessen werden konnte, steht das dabei. Eine benannte Lücke ist besser als
eine, die nach Vollständigkeit aussieht.

---

## Dokumente

| | |
|---|---|
| **[`docs/SOFTWARE_VON_GRUND_AUF.md`](docs/SOFTWARE_VON_GRUND_AUF.md)** | **1 · Zuerst lesen: Wie man eine Software von Grund auf baut** — die Grundkonzepte, ohne technische Tiefe (Anhang B der Arbeit) |
| [`docs/README.md`](docs/README.md) | **Die Karte aller Dokumente** — welches man liest, wenn man etwas Bestimmtes sucht |
| [`docs/PRODUKT_DIE_SCHRITTE.md`](docs/PRODUKT_DIE_SCHRITTE.md) | **Was Visbox heute kann, Schritt für Schritt** — für den Owner geschrieben, in jeder Bau-Sitzung fortgeschrieben |
| [`docs/PLAN.md`](docs/PLAN.md) | Vorgehensplan, Phasen 0–4, **offene Wissensschulden** — in jeder Sitzung fortgeschrieben |
| [`docs/PLAN_AB_2026-09-01.md`](docs/PLAN_AB_2026-09-01.md) | **Der Plan ab 1.9.2026: Rückstand zuerst** — zwei Wochen nichts Neues bauen |
| [`docs/LAGEBEURTEILUNG_2026-08-14.md`](docs/LAGEBEURTEILUNG_2026-08-14.md) | Bestandsaufnahme der Bausteine mit Lizenzprüfung |
| [`docs/LIZENZPRUEFUNG_2026-08-18.md`](docs/LIZENZPRUEFUNG_2026-08-18.md) | 38 Positionen gegen die Primärquelle |
| [`docs/LIZENZPRUEFUNG_BINAER_2026-08-18.md`](docs/LIZENZPRUEFUNG_BINAER_2026-08-18.md) | was Binärpakete mitbringen und ihre Wheel-Angabe verschweigt |
| [`docs/SCHWELLENSTUDIE_2026-08-18.md`](docs/SCHWELLENSTUDIE_2026-08-18.md) | Kalibrierung der Geometrie-Schwelle |
| [`docs/EINBINDUNG_KOSMOORBIT_2026-08-14.md`](docs/EINBINDUNG_KOSMOORBIT_2026-08-14.md) | der MCP-Vertrag und was er für die Bauform bedeutet |
| **[`docs/EINBAU_CLOUDWORKER_2026-08-22.md`](docs/EINBAU_CLOUDWORKER_2026-08-22.md)** | **FÜR DEN CLOUD-WORKER:** was hier fertig ist und die KosmoOrbit-Seite **nicht erreicht** — mit dem, was dort dafür zu bauen wäre |
| [`docs/UEBERGABE_VIS_2026-08-19.md`](docs/UEBERGABE_VIS_2026-08-19.md) | die ausführliche Fassung: 14 Fragen an die Vis-Oberfläche, mit Begründung |
| [`docs/TOTE_KANTEN_TRIAGE_2026-08-26.md`](docs/TOTE_KANTEN_TRIAGE_2026-08-26.md) | 80 Funktionen ohne Aufrufer, jede mit einem Urteil — und drei, die eines brauchen |
| [`docs/ENTSCHEIDE_VISBOX_2026-09-18.md`](docs/ENTSCHEIDE_VISBOX_2026-09-18.md) | die Entscheide zur eigenen Software (E1–E27) |
| [`docs/ENTSCHEIDE_IPAD_2026-09-21.md`](docs/ENTSCHEIDE_IPAD_2026-09-21.md) | die Entscheide zur iPad-App |
| [`docs/LEXIKON.md`](docs/LEXIKON.md) | Fachbegriffe für Leser:innen mit Architekturhintergrund |
| [`docs/sitzungen/`](docs/sitzungen/) | Sitzungsprotokolle: Entscheidungen **mit Begründung** |
| [`NOTICE`](NOTICE) | fremde Komponenten samt Lizenz und Prozessgrenze |

Das [`LEXIKON`](docs/LEXIKON.md) ist Anhang der Arbeit, kein Nebenprodukt: Es erklärt jeden
nicht-architektonischen Fachbegriff für Leser:innen ohne Informatikhintergrund.

### Wer an KosmoOrbit baut, fängt hier an

[`docs/EINBAU_CLOUDWORKER_2026-08-22.md`](docs/EINBAU_CLOUDWORKER_2026-08-22.md) listet die
Stellen, an denen **diese Seite mehr weiss, als sie der Vis-Oberfläche sagen kann.** Die
Verbindung zwischen beiden ist ausschliesslich die Brücke über Dateien in
`/tmp/kosmo-jobs/` — kein gemeinsamer Code. Was dort kein Feld im Vertrag hat, kommt drüben
nicht an, egal wie fertig es hier ist.

Der wichtigste Punkt daraus: **Die Geometrie-Zahlen, die der Vertrag heute trägt, haben wir
selbst als unbrauchbar gemessen** — `geom_iou` belohnt ein Bild ohne Bauwerk, und der Score
ist nicht monoton im Fehler. Was stattdessen trägt, ist gebaut und hat drüben kein Feld.

*Stand 29.09.2026:* Das Blatt ist eine Momentaufnahme vom 22.08. Seither ist das Feld dafür
**vereinbart**, aber noch nicht gebaut: `geometry_gates` steht in ihren Wörtern in unserem
Ergebnis, und KosmoOrbit nimmt es in den Vertrag auf, sobald ein gemessenes Beispiel
vorliegt. Antworten und Aufträge für den Cloud-Worker legen wir seit dem 29.09. direkt in
seinen Eingangsordner in **ihrem** Repo — er hat unseres nicht, und ein Blatt, das nur bei
uns liegt, ist nicht zugestellt.

---

## Entwicklung

Voraussetzung: Python 3.11 oder neuer. **Das Paket deklariert keine
Laufzeitabhängigkeiten**, und das ist Absicht: Die gesamte Testsammlung und die ganze
QA-Kette laufen ohne sie.

*Was das nicht heisst:* Die Bildmodell- und die Schätzstufe importieren `torch`,
`diffusers` und `transformers` sehr wohl — verzögert, aber **in denselben Prozess**. Die
Prozessgrenze in diesem Projekt trennt nach **Lizenz**, nicht nach Gewicht: Jenseits von
ihr liegt, was copyleft ist (Blender, IfcOpenShell). `torch` ist BSD-3-Clause und braucht
sie nicht.

**Testgeometrie erzeugen.** Das Repo enthält keine IFC-Datei; sie wird erzeugt (Regel 3):

```
python3 tools/make_test_ifc.py build/testbau.ifc
```

**Environment hinter der Prozessgrenze anlegen.** `ifcopenshell` steht unter LGPL und
bringt statisch gelinkten GPL-Code mit (CGAL, am Binary verifiziert). Deshalb liegt es in
einem *eigenen* Environment und wird als Subprozess aufgerufen, nie in den Kern importiert:

```
python3 -m venv .venv-ifc && .venv-ifc/bin/pip install ifcopenshell trimesh numpy
```

**Tests laufen lassen** — sie brauchen keine GPU:

```
python3 -m pytest
```

### Umgebungsvariablen

Alle zeigen auf etwas jenseits der Prozessgrenze. Für die ersten drei gibt es einen
Rückfall auf die üblichen Orte; für die beiden letzten **bewusst nicht** — ein Rückfall
auf das Produkt-Python würde genau die Grenze aufheben, die es zu ziehen gilt.

| Variable | wofür | ohne sie |
|---|---|---|
| `AIIMAGING_IFC_PYTHON` | Python des IFC-Environments | `.venv-ifc/bin/python` |
| `AIIMAGING_BLENDER` | das Blender-Binary | `blender` im PATH, dann `/opt/blender/blender` |
| `AIIMAGING_MODELLE` | Ablage der Modellgewichte | `/ai`, **falls es den Ordner gibt** — sonst der Anwendungsdatenordner des Systems: macOS `~/Library/Application Support/Visbox/modelle`, Windows `%LOCALAPPDATA%\Visbox\modelle`, sonst `$XDG_DATA_HOME/visbox/modelle` |
| `AIIMAGING_LORA_PYTHON` | Python des Trainer-Environments | **Fehler**, kein Rückfall |
| `AIIMAGING_LORA_TRAINER` | Verzeichnis des LoRA-Trainers | **Fehler**, kein Rückfall |

Und eine, die nichts adressiert, sondern eine Uhr stellt:

| Variable | wofür | ohne sie |
|---|---|---|
| `AIIMAGING_ZEITFAKTOR` | streckt **alle** Zeitgrenzen auf einmal — die Gesamtfristen und den Anlauf, den ein kalter Blender-Start braucht | Faktor `1.0`, also jede Zahl unverändert |

Die Zahlen dahinter (300 s für einen IFC-Import, 900 s für einen Render, 60 s Anlauf) sind
auf einer schnellen Maschine **gemessen**. Auf einem Laptop wäre dieselbe Frist ein
Abbruch mitten in einer gesunden Rechnung — und der sieht aus wie ein Fehler, obwohl nur
die Uhr zu knapp stand. `AIIMAGING_ZEITFAKTOR=3` verdreifacht sie alle; bei `1.0` kommt
jede Zahl typgleich und unverändert zurück, geprüft.

Und eine, die eine Tür öffnet, und zwar nur für die Forschung:

| Variable | wofür | ohne sie |
|---|---|---|
| `AIIMAGING_FORSCHUNGSMODELLE` | erlaubt, ein Modell unter Forschungslizenz zu laden (heute nur Qwen-Image-2.1) — nur an der HomeStation, nur für einen Messlauf, **nie dauerhaft**. Wirkt nur beim Wert genau `1` | Forschungsmodelle laden nicht; alles andere unverändert |

### Aufträge an eine Maschine mit GPU

Dieses Environment hat keine GPU. Was eine braucht, läuft über das Repo als Übergabeort —
ein Auftrag ist eine Datei, ein Ergebnis ist eine Datei, kein Netzwerkdienst. Siehe
[`auftraege/README.md`](auftraege/README.md).

---

## Lizenz

Apache-2.0 — siehe [`LICENSE`](LICENSE). Fremde Komponenten und ihre Lizenzen stehen im
[`NOTICE`](NOTICE). Was copyleft ist (Blender, IfcOpenShell), wird nie eingebaut, sondern
nur über eine Prozessgrenze aufgerufen. Mitgeliefert werden nur permissive Bausteine — die
MIT-Bibliotheken der Knotenansicht und, als einzige Ausnahme nach Regel 1, Schriften unter
der OFL. Forschungsmodelle werden nicht ausgeliefert.
