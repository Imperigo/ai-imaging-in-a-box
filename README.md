# ai-imaging-in-a-box

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

**Stand 2026-08-26.** Die Kette läuft von einer IFC-Datei bis zum bewerteten Bild, und sie
ist am Gerät gelaufen: Der erste echte Render mit echten Modellgewichten fand am
18.08.2026 statt (`auf-20260818-09`, Qwen-Image-Edit-2511, 147,9 s, Score 0,359 —
durchgefallen, und das ist ein Messwert und kein Fehlschlag).

**Was in diesem Environment messbar ist, und was nicht** — nachgesehen am 26.08.2026, weil
die Kurzform *«hier gibt es keine GPU»* zu der falschen Folgerung verleitet, hier lasse
sich gar nichts messen:

| | |
|---|---|
| **Hier** | Blender (`/opt/blender/blender`) und `.venv-ifc`. Also die **ganze Geometrieseite**: IFC → glb, Multipass, Kamerastellung, Hüllboxen, Sonne, Rahmung |
| **Nur auf der Arbeitsstation** | alles, was `torch` braucht: die **Diffusion** und der **Tiefenschätzer** — und damit die Geometrie-Treue-Zahl selbst |

*Der Unterschied hat an einem einzigen Tag zwei Befunde freigelegt*, die vorher als
„braucht die Arbeitsstation" galten: dass der Deckungsgrad unter 8 m Kantenlänge gar nicht
bindet, und dass die Bauwerksbox das Gelände nicht abtrennte.

Die Lücke, die bleibt, ist eine andere und schmalere: **Ein Bild, das die
Geometrie-Schwelle besteht, gibt es noch nicht** — mit einem Prompt ohne Bauteile und
einer Geometrie, die ein Gebäude ist statt einer offenen Schachtel. Bis dahin ist die
Kette belegt, die Aussage *geometrietreu* aber noch nicht.

| | Stand |
|---|---|
| IFC → glb, über die Prozessgrenze | läuft, an 40 echten Dateien gemessen. **Seit 26.08. trägt der Knotenname den IFC-Namen** — ohne ihn war das Gelände auf der Blender-Seite nicht abtrennbar |
| glb → Blender-Multipass (Beauty, Material-ID, Tiefe) | läuft auf Blender 4.2 **und** 5.2 |
| Bildmodell-Stufe (`diffusers`) | **am Gerät gelaufen** (18.08.); am 25.08. bis in die Diffusion, dort an einem Gerätekonflikt gescheitert — Ursache gefunden, Fix eingebaut, Bestätigung beauftragt |
| Geometrie-Treue-Metrik | gebaut und kalibriert |
| Prüfungen **vor** dem Bildlauf | seit 26.08.: Rahmung, Kamerahöhe, Zwischenbilder, Doppelansicht — **Massstab meldet, bricht noch nicht ab**. Die Rahmung rechnet mit dem **gemessenen** Füllgrad des Laufs, nicht mit dem Sollwert |
| Stil-Gate | gebaut, Schwelle ungeprüft |
| Kette als Graph mit Zwischenspeicher | gebaut und **gemessen** (Prompt-Änderung rechnet die Geometriestufen nicht neu) — aber **nicht am Produktivweg**: der Abholer fährt die Stufen als gerade Abfolge |
| MCP-Anbindung an KosmoOrbit | **registriert am 18.08.** (Odysseus, `id d99fcf67`, alle Werkzeuge antworteten) — seither kamen ein viertes Werkzeug und die Ausführung dazu, beides am Gerät noch unbestätigt |
| Ein über KosmoOrbit bestellter Render | **seit 26.08. wird er auch ausgeführt.** Bis dahin legte der MCP-Einlass ihn in einem Verzeichnis ab, das niemand las: Er ging mit Freigabe auf `queued` und blieb dort. Beide Wege gehen jetzt durch denselben Abholer und damit durch dieselben Riegel |
| LoRA-Stiltraining | Naht gebaut, **nie ein Training ausgeführt** |

**Wie weit der Einbau in KosmoOrbit ist**, Posten für Posten mit Datum und Beleg:
[`docs/EINBAU_STAND.md`](docs/EINBAU_STAND.md). Wie die Oberfläche aussehen soll, die
darüber liegt: [`docs/OBERFLAECHE_KOSMOVIS.md`](docs/OBERFLAECHE_KOSMOVIS.md). Was uns
bei der eigenen Arbeit an der Oberfläche auffällt und an den UI-Worker geht:
[`docs/UI_BEFUNDE.md`](docs/UI_BEFUNDE.md).

Tests: **4835**, alle grün, ohne GPU. *Die Zahl steht unter einem Wächter
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
   Test prüft.
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
| [`docs/PLAN.md`](docs/PLAN.md) | Vorgehensplan, Phasen 0–4, **offene Wissensschulden** |
| [`docs/PLAN_AB_2026-09-01.md`](docs/PLAN_AB_2026-09-01.md) | **Der Plan ab 1.9.2026: Rückstand zuerst** — zwei Wochen nichts Neues bauen |
| [`docs/LAGEBEURTEILUNG_2026-08-14.md`](docs/LAGEBEURTEILUNG_2026-08-14.md) | Bestandsaufnahme der Bausteine mit Lizenzprüfung |
| [`docs/LIZENZPRUEFUNG_2026-08-18.md`](docs/LIZENZPRUEFUNG_2026-08-18.md) | 38 Positionen gegen die Primärquelle |
| [`docs/LIZENZPRUEFUNG_BINAER_2026-08-18.md`](docs/LIZENZPRUEFUNG_BINAER_2026-08-18.md) | was Binärpakete mitbringen und ihre Wheel-Angabe verschweigt |
| [`docs/SCHWELLENSTUDIE_2026-08-18.md`](docs/SCHWELLENSTUDIE_2026-08-18.md) | Kalibrierung der Geometrie-Schwelle |
| [`docs/EINBINDUNG_KOSMOORBIT_2026-08-14.md`](docs/EINBINDUNG_KOSMOORBIT_2026-08-14.md) | der MCP-Vertrag und was er für die Bauform bedeutet |
| **[`docs/EINBAU_CLOUDWORKER_2026-08-22.md`](docs/EINBAU_CLOUDWORKER_2026-08-22.md)** | **FÜR DEN CLOUD-WORKER:** was hier fertig ist und die KosmoOrbit-Seite **nicht erreicht** — mit dem, was dort dafür zu bauen wäre |
| [`docs/UEBERGABE_VIS_2026-08-19.md`](docs/UEBERGABE_VIS_2026-08-19.md) | die ausführliche Fassung: 14 Fragen an die Vis-Oberfläche, mit Begründung |
| [`docs/TOTE_KANTEN_TRIAGE_2026-08-26.md`](docs/TOTE_KANTEN_TRIAGE_2026-08-26.md) | 80 Funktionen ohne Aufrufer, jede mit einem Urteil — und drei, die eines brauchen |
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

Alle zeigen auf etwas jenseits der Prozessgrenze. Für die ersten beiden gibt es einen
Rückfall auf die üblichen Orte; für die übrigen **bewusst nicht** — ein Rückfall auf das
Produkt-Python würde genau die Grenze aufheben, die es zu ziehen gilt.

| Variable | wofür | ohne sie |
|---|---|---|
| `AIIMAGING_IFC_PYTHON` | Python des IFC-Environments | `.venv-ifc/bin/python` |
| `AIIMAGING_BLENDER` | das Blender-Binary | `blender` im PATH, dann `/opt/blender/blender` |
| `AIIMAGING_MODELLE` | Ablage der Modellgewichte | `/ai` |
| `AIIMAGING_LORA_PYTHON` | Python des Trainer-Environments | **Fehler**, kein Rückfall |
| `AIIMAGING_LORA_TRAINER` | Verzeichnis des LoRA-Trainers | **Fehler**, kein Rückfall |

### Aufträge an eine Maschine mit GPU

Dieses Environment hat keine GPU. Was eine braucht, läuft über das Repo als Übergabeort —
ein Auftrag ist eine Datei, ein Ergebnis ist eine Datei, kein Netzwerkdienst. Siehe
[`auftraege/README.md`](auftraege/README.md).

---

## Lizenz

Apache-2.0 — siehe [`LICENSE`](LICENSE). Fremde Komponenten und ihre Lizenzen stehen im
[`NOTICE`](NOTICE); keine davon wird eingebaut, alle werden über eine Prozessgrenze
aufgerufen.
