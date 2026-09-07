# Die Dokumente — eine Karte

Neunundsechzig Dateien liegen hier, dazu dreiundzwanzig Sitzungsprotokolle. Diese Karte
sagt, **welche man liest, wenn man etwas Bestimmtes sucht** — und welche man getrost
liegen lässt, weil eine spätere sie überholt hat.

*Warum es sie gibt:* Ein Ordner mit neunundsechzig gleichrangig aussehenden Dateien ist
kein Nachschlagewerk, sondern ein Stapel. Wer darin die richtige Datei nur findet, wenn er
schon weiss, wie sie heisst, findet sie nicht.

**Seit dem 09.09.2026 gibt es eine zweite Hilfe, und sie steht in den Dateien selbst:**
Jedes Sitzungsprotokoll und jeder lange Abschnitt von `PLAN.md` trägt oben eine
**Deckelzeile** — was entschieden wurde, was gemessen wurde, was offen blieb. Sie ist
gelesen und nicht erzeugt, und `tests/test_plan.py` hält fest, dass sie da ist.

**Die Karte ersetzt keine Datei und fasst keine zusammen.** Sie ordnet.

---

## Wenn du nur drei Dinge liest

| Datei | wofür |
|---|---|
| [`LEXIKON.md`](LEXIKON.md) | Jeder Fachbegriff des Projekts, für Leser:innen ohne Informatikhintergrund. Anhang der Vertiefungsarbeit, kein Nebenprodukt. |
| [`EINBAU_STAND.md`](EINBAU_STAND.md) | Was von KosmoVis wirklich in KosmoOrbit läuft — je Posten mit Adressat und Beleg. Die ehrlichste Seite des Projekts. |
| [`PLAN_AB_2026-09-01.md`](PLAN_AB_2026-09-01.md) | Der laufende Plan, täglich fortgeschrieben. Erledigtes wird abgehakt, nicht gelöscht. |

---

## Bausteine der Arbeit — hier steht ein Ergebnis

Diese Dateien tragen **Messungen und Entscheidungen**. Sie sind das Material der
Vertiefungsarbeit, nicht ihr Arbeitsprotokoll.

### Was das Bild misst, und wo die Masse versagen

| Datei | Ergebnis in einem Satz |
|---|---|
| [`SCHWELLENSTUDIE_2026-08-18.md`](SCHWELLENSTUDIE_2026-08-18.md) | Kalibrierung der Geometrie-Metrik an synthetischer Geometrie — der erste Anlauf. |
| [`SCHWELLENSTUDIE_ECHT_2026-08-26.md`](SCHWELLENSTUDIE_ECHT_2026-08-26.md) | **Dieselbe Kalibrierung auf echter Geometrie.** Wer nur eine der beiden liest, liest diese. |
| [`GEOM_IOU_HALLUZINATION_2026-08-21.md`](GEOM_IOU_HALLUZINATION_2026-08-21.md) | `geom_iou` fängt die Abwesenheit nicht — bei viel Boden belohnt es sie sogar. |
| [`HALLUZINATION_2026-08-21.md`](HALLUZINATION_2026-08-21.md) | Die Gegenprobe: `geom_iou` darf trotzdem nicht fallen. |
| [`MASKE_2026-08-21.md`](MASKE_2026-08-21.md) | Es liegt am Boden — aber die Heilung heisst nicht «ρ über der Maske». |
| [`BODENANTEIL_2026-08-26.md`](BODENANTEIL_2026-08-26.md) | Wie stumpf die Maske wird, wenn der Boden darin steckt. |
| [`DECKELSTUDIE_2026-08-26.md`](DECKELSTUDIE_2026-08-26.md) | Woran `geom_iou` deckelt — und woran nicht. |
| [`GEOM_IOU_BODEN_UND_DECKE_2026-08-27.md`](GEOM_IOU_BODEN_UND_DECKE_2026-08-27.md) | Der Boden gehört der Szene, die Decke sieht nicht hinein. |
| [`BRAUCHT_ES_GEOM_IOU_2026-08-26.md`](BRAUCHT_ES_GEOM_IOU_2026-08-26.md) | Fängt der Maskenweg, was `geom_iou` fängt? |
| [`EMPFINDLICHKEIT_2026-08-20.md`](EMPFINDLICHKEIT_2026-08-20.md) | Die Normierung trägt nicht, und die Metrik ist zu stumpf. |
| [`RANDKANTE_2026-08-22.md`](RANDKANTE_2026-08-22.md) | Die fehlende Randkante ist ein echter Mangel — und das Mass lässt sich schärfen. |
| [`NACHBARGEBAEUDE_2026-09-02.md`](NACHBARGEBAEUDE_2026-09-02.md) | Ein geerbter Vorbehalt, nachgerechnet: Er gilt für den **Schätzer**, nicht für die Szene. |
| [`GELAENDEFORM_2026-09-07.md`](GELAENDEFORM_2026-09-07.md) | Gelände an der **Form** erkennen, wenn der Name es nicht trägt — und was die Schwellen in beiden Fehlerrichtungen kosten. |
| [`NAMENSDECKUNG_2026-09-08.md`](NAMENSDECKUNG_2026-09-08.md) | Sehen Box- und Bildseite dieselben Namen? Materialnamen **0 %**, Objektnamen 100 % — und Blenders Dublettensuffix bricht es auf 25 %. |

### Die Paarschwellen

| Datei | Ergebnis in einem Satz |
|---|---|
| [`PAARSCHWELLEN_OBERGRENZE_2026-08-27.md`](PAARSCHWELLEN_OBERGRENZE_2026-08-27.md) | Können die Paarmasse überhaupt trennen? Obergrenze ohne Schätzer. |
| [`PAARSCHWELLEN_OBERGRENZE_2026-09-01.md`](PAARSCHWELLEN_OBERGRENZE_2026-09-01.md) | **Die Ersatzkalibrierung** — vier Szenen, vier Richtungen, und was `0.80` kostet. Die jüngere der beiden. |
| [`RICHTUNGEN_2026-08-28.md`](RICHTUNGEN_2026-08-28.md) | Hängt die Messbarkeit am Standpunkt? Acht Richtungen, dieselbe Szene. |
| [`ENTSCHEIDUNGEN_2026-09-02.md`](ENTSCHEIDUNGEN_2026-09-02.md) | Zwei Owner-Entscheidungen, gemessen vorbereitet — **und eine davon ist ausdrücklich noch nicht dran.** |

### Kamera und Standpunkt

| Datei | Ergebnis in einem Satz |
|---|---|
| [`KAMERAREGELN_2026-08-21.md`](KAMERAREGELN_2026-08-21.md) | Was die Recherche für unsere Kamera bedeutet. |
| [`KAMERABLICK_2026-08-19.md`](KAMERABLICK_2026-08-19.md) | Zwölf Bilder angesehen — was zwölf grüne Zahlen nicht zeigten. |
| [`KAMERANEIGUNG_2026-08-22.md`](KAMERANEIGUNG_2026-08-22.md) | Die Neigung stört den Schätzer nicht; der erste Anlauf war der lehrreichere. |
| [`STANDPUNKTE_2026-09-01.md`](STANDPUNKTE_2026-09-01.md) | Was `guete_standpunkt` wirklich unterscheidet: acht Standpunkte, **zwei** Werte. |

### Die Bildkette — ControlNet, Polarität, Seed

| Datei | Ergebnis in einem Satz |
|---|---|
| [`BACKBONE_CONTROLNET_2026-08-18.md`](BACKBONE_CONTROLNET_2026-08-18.md) | Kandidatenprüfung für einen Backbone mit echter Depth-Naht. |
| [`CONTROLNET_NAHT_2026-08-20.md`](CONTROLNET_NAHT_2026-08-20.md) | Die Naht trägt — aber sie trägt etwas anderes als gedacht. |
| [`DIE_SCHABLONE_2026-08-20.md`](DIE_SCHABLONE_2026-08-20.md) | **Das ControlNet hat nie eine Tiefenkarte gesehen.** |
| [`BACKBONE_2026-08-22.md`](BACKBONE_2026-08-22.md) | Nicht der Backbone war es — die Schablone war es. |
| [`TIEFENKANTE_2026-08-21.md`](TIEFENKANTE_2026-08-21.md) | Der Prüfstein fällt, und der Kandidat lebt trotzdem. |
| [`POLARITAET_2026-08-21.md`](POLARITAET_2026-08-21.md) | Die Richtung repariert einen der drei Knicke — die Stumpfheit gar nicht. |
| [`POLARITAET_UND_STAERKE_2026-08-22.md`](POLARITAET_UND_STAERKE_2026-08-22.md) | **Die Polarität ist entschieden, die Stärke nicht** — der jüngere Stand. |
| [`SEEDAUSWAHL_2026-08-22.md`](SEEDAUSWAHL_2026-08-22.md) | Der billigste Qualitätssprung, den die Kette heute hergibt. |
| [`RAUSCHBODEN_2026-08-20.md`](RAUSCHBODEN_2026-08-20.md) | Der Rauschboden — und warum er die Frage noch nicht beantwortet. |
| [`RAUSCHBODEN_MIT_BODEN_2026-08-20.md`](RAUSCHBODEN_MIT_BODEN_2026-08-20.md) | Derselbe Versuch mit Boden: ein Score, der nichts wert ist. |
| [`STILSTUDIE_2026-08-18.md`](STILSTUDIE_2026-08-18.md) | Was an der Stil-Schwelle 0,30 messbar ist — und was nicht. |
| [`EICHUNG_2026-08-23.md`](EICHUNG_2026-08-23.md) | Eichung der Geometrie-Masse. |

### Geometrie und IFC

| Datei | Ergebnis in einem Satz |
|---|---|
| [`BEFUND_2026-08-24_IFC-LESER.md`](BEFUND_2026-08-24_IFC-LESER.md) | Zwei IFC-Leser an derselben Datei — und was sie unterschiedlich sehen. |
| [`BEFUND_2026-08-24_ORTSFELD.md`](BEFUND_2026-08-24_ORTSFELD.md) | Das Ortsfeld ist stabil — und es ist eine Schüssel. |
| [`BLENDER_AUSGABETAKT_2026-08-20.md`](BLENDER_AUSGABETAKT_2026-08-20.md) | Blenders Standardausgabe taugt nicht als Fortschrittszeichen. |

---

## Lizenz und Ökosystem — die Regel-1-Seite

| Datei | wofür |
|---|---|
| [`LIZENZPRUEFUNG_2026-08-18.md`](LIZENZPRUEFUNG_2026-08-18.md) | Die Sekundärquellen aus Kapitel 9, gegen das Original gehalten. |
| [`LIZENZPRUEFUNG_BINAER_2026-08-18.md`](LIZENZPRUEFUNG_BINAER_2026-08-18.md) | **Was die Binärpakete mitbringen — und was ihre Wheel-Angabe verschweigt.** Die zweite ergänzt die erste; keine ersetzt die andere. |
| [`OEKOSYSTEM_2026-08-18.md`](OEKOSYSTEM_2026-08-18.md) | Das Ökosystem gelesen, und wo unser Code nicht hineinpasst. |
| [`LAGEBEURTEILUNG_2026-08-14.md`](LAGEBEURTEILUNG_2026-08-14.md) | Der erste Auftrag überhaupt: je offener Baustein die Lizenz, GPL/AGPL-Funde ausdrücklich benannt. |
| [`BLENDER_ADDON_BESTAND_2026-08-18.md`](BLENDER_ADDON_BESTAND_2026-08-18.md) | Der ältere Add-on-Code — Bestandsaufnahme unter Regel 2. |
| [`KI_MODULE_BESTAND_2026-08-19.md`](KI_MODULE_BESTAND_2026-08-19.md) | Die beiden ungeöffneten KI-Module des Altbestands. |

---

## Die Naht zu KosmoOrbit

| Datei | wofür |
|---|---|
| [`EINBAU_STAND.md`](EINBAU_STAND.md) | Der Stand je Posten, mit Adressat und Beleg. |
| [`EINBINDUNG_KOSMOORBIT_2026-08-14.md`](EINBINDUNG_KOSMOORBIT_2026-08-14.md) | Vertrag und Folgen für den Entwurf. |
| [`EINBAU_CLOUDWORKER_2026-08-22.md`](EINBAU_CLOUDWORKER_2026-08-22.md) | Was bei uns fertig ist und die andere Seite nicht erreicht. |
| [`UEBERGABE_VIS_2026-08-19.md`](UEBERGABE_VIS_2026-08-19.md) | Übergabeblatt an die Vis-Oberfläche. |
| [`RENDERAUFTRAG_ENTWURF_2026-08-19.md`](RENDERAUFTRAG_ENTWURF_2026-08-19.md) | Der Renderauftrag, Entwurf zur Entscheidung. |
| [`OBERFLAECHE_KOSMOVIS.md`](OBERFLAECHE_KOSMOVIS.md) | Entwurf der KosmoVis-Oberfläche. |
| [`UI_BEFUNDE.md`](UI_BEFUNDE.md) | Gesammelte Oberflächen-Befunde aus der eigenen Arbeit. |
| [`COCKPIT_BESTAND_2026-08-19.md`](COCKPIT_BESTAND_2026-08-19.md) | Wo die Oberfläche der Demo-Vision technisch lebt. |
| [`WELCHE_APP_2026-08-19.md`](WELCHE_APP_2026-08-19.md) | Vier Bestände, und keiner ist sicher der richtige. |

---

## Arbeitsprotokolle — Verlauf, nicht Ergebnis

Sie halten fest, **was an einem Tag geschah**. Für ein Ergebnis sind sie der falsche Ort;
für die Frage «warum wurde das so entschieden» der richtige.

* [`sitzungen/`](sitzungen/) — zwanzig Sitzungsprotokolle, `JJJJ-MM-TT_sitzung-NN.md`.
  Entscheidungen **mit Begründung**, korrigierte Fehlannahmen, Prüfwege, offene Punkte.
* `HOMESTATION-*.md` (acht Dateien) — was auf der Maschine mit GPU tatsächlich lief.
  Die drei `DEMO-SIMULATION`-Dateien (19.08., 20.08., 24.08.) sind drei Durchgänge
  desselben Versuchs; **der jüngste ist der gültige**, die älteren zeigen den Weg dahin.
* [`ABHOLER_ERSTER_LAUF_2026-08-19.md`](ABHOLER_ERSTER_LAUF_2026-08-19.md) — der erste
  Auftrag, der wirklich durchlief, und das Minuszeichen, das ihn elf Stunden aufhielt.
* [`TOTE_KANTEN_TRIAGE_2026-08-26.md`](TOTE_KANTEN_TRIAGE_2026-08-26.md) — Triage der
  toten Kanten.

---

## Pläne — der jüngste gilt

`PLAN.md` ist der Vorgehensplan über alles; die datierten Pläne sind Tagespläne und
**überholt, sobald ein jüngerer danebensteht**. Gelöscht wird keiner: Ein abgehakter Plan
zeigt, was man an dem Tag für wichtig hielt, und das ist selbst ein Befund.

| Datei | Stand |
|---|---|
| [`PLAN.md`](PLAN.md) | der Vorgehensplan über alles — **offene Punkte und tragende Befunde** |
| [`erledigt/PLAN_bis_2026-08-28.md`](erledigt/PLAN_bis_2026-08-28.md) | das Archiv: 22 vollständig abgehakte Abschnitte, unverändert, **wird nicht fortgeschrieben** |
| [`PLAN_AB_2026-09-01.md`](PLAN_AB_2026-09-01.md) | **der laufende** |
| `PLAN_2026-08-24.md`, `PLAN_2026-08-21.md`, `PLAN_2026-08-20.md` | überholt, in dieser Reihenfolge |
| [`DEMOPLAN_2026-08-18.md`](DEMOPLAN_2026-08-18.md) | Plan zur Semester-Demo |

---

## Was hier NICHT liegt

* **Aufträge** stehen in [`../auftraege/`](../auftraege/) — offene, Ergebnisse, und unter
  `bloecke/` die Blöcke für Adressaten, die das Repo nicht lesen.
* **Der Code** steht unter `../src/aiimaging/`, seine Wächter unter `../tests/`.
* **Bilder, Geometrie, Modellgewichte** liegen grundsätzlich **nicht** im Repo (Regel 3).
  Ein Dokument, das Zahlen aus einem Lauf nennt, nennt Zahlen — nicht die Datei.
