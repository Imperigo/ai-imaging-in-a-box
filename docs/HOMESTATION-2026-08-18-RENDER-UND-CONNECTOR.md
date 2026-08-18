# HomeStation, 18.08.2026: erster echter Render und der erste Kontakt mit echten Dateien

**Home-PC-Worker.** Gefahren wurden `auf-20260818-08` (Connector-Schicht an echter
Architekturgeometrie) und `auf-20260818-09` (erster echter Render). Beides gemessen, nicht
geschlossen. Dieses Dokument hält fest, was daran über den Tag hinaus gilt.

---

## 1 · Was die Karte wirklich hergibt

| Weg | VRAM | Ergebnis |
|---|---|---|
| alles resident (`.to("cuda")`) | 29,57 GiB belegt | **Abbruch** — OOM bei einer Anforderung von 18 MiB |
| komponentenweise (`enable_model_cpu_offload`) | 29,34 GiB belegt | **Abbruch** — OOM |
| schichtweise (`enable_sequential_cpu_offload`) | **2,86 GiB Spitze** | **läuft**, 189 s |

Die RTX 5090 hat 31,36 GiB nutzbar. Entscheidend ist nicht die Summe der Gewichte
(53,8 GiB auf Platte), sondern die **grösste einzelne Komponente**: Der Transformer von
Qwen-Image-Edit-2511 ist allein 38,05 GiB. Er passt an keinem Stück auf diese Karte, und
darum hilft komponentenweises Auslagern nicht — es schiebt genau diesen einen Block hin
und her, der nicht hineingeht. Wer nur die Summe prüft, wählt die mittlere Stufe und
scheitert ein zweites Mal.

**Das Wesentliche für die Planung:** Mit 2,86 GiB Spitze können Bildmodell und ein
30B-Q4-Sprachmodell **gleichzeitig** resident sein. Das war die offene Frage aus auf-07,
und die Antwort ist ja — aber erkauft mit Rechenzeit, nicht geschenkt.

Aufteilung der Gewichte auf Platte:

```
transformer    38,05 GiB     text_encoder   15,45 GiB
vae             0,24 GiB     processor       0,01 GiB
```

## 2 · Qwen-Image-Edit-2511 ist kein ControlNet

`QwenImageEditPlusPipeline.__call__` kennt **weder `control_image` noch
`controlnet_conditioning_scale` noch `strength`**. Sie nimmt `image`, `prompt`,
`negative_prompt`, `true_cfg_scale`, `num_inference_steps`, `generator`.

Das hat zwei Folgen, und die zweite ist die unangenehmere:

1. Die Konditionierung ist **Bildbearbeitung, nicht ControlNet**. Die Tiefenkarte geht als
   `image` hinein und ersetzt dabei den Beauty-Pass — es gibt nur einen Bildeingang.
2. **`controlnet_staerke` und `denoise` werden nicht verbraucht.** Die geplante
   Vergleichsreihe mit 0,6 / 0,8 / 1,0 hätte dreimal dasselbe Bild geliefert. Drei
   identische Bilder unter drei verschiedenen Parametern sehen aus wie ein Befund
   («die Stärke wirkt nicht») und wären keiner gewesen, sondern ein Messfehler.

Der Registry-Eintrag führt dieses Backbone unter `konditionierung = depth_controlnet`.
Das trifft für diese Pipeline nicht zu und gehört korrigiert — die Entscheidung darüber
liegt beim Modul-Eigner, hier steht nur der Messwert.

## 3 · Was am Bild zu sehen ist, und was die Metrik dazu sagt

Die Testgeometrie (`tools/make_test_ifc.py`) ist eine **oben offene Schachtel**:
Tiefenkarte und Beauty-Pass zeigen beide einen kleinen Kasten in der Bildmitte, in den
man hineinsieht, auf leerem Grund.

**Im Render ist beides verloren gegangen.** Erstens hat das Modell ein Dach erfunden —
der Prompt verlangt eines (*«clean flat roof»*), die Geometrie hat keines, und das Modell
ist dem Prompt gefolgt. Zweitens hat es den Bildausschnitt neu gewählt: Der Quader füllt
das Bild formatfüllend, mit Bodenebene und Horizont, wo die Vorgabe einen kleinen Körper
in der Mitte zeigt.

Der vollständige Messlauf (Lauf 9, `status: ok`, `gemessen: true`) bestätigt das Auge:

| Messwert | Wert |
|---|---|
| **score** | **0,359** (Schwelle 0,65 → nicht bestanden) |
| spearman | **−0,339** (gewertet als Betrag 0,339) |
| geom_iou | 0,380 |
| n_gemeinsam | 24 575 Punkte |

Die getrennten Werte sagen mehr als der Score: **geom_iou 0,38** heisst, die Silhouette
sitzt woanders — das ist der neu gewählte Ausschnitt. Das **negative** spearman heisst,
die Tiefenordnung ist invertiert; die eingebaute Warnung nennt selbst die zwei
ununterscheidbaren Deutungen (Disparitätskonvention des Schätzers oder echte
Vorne-hinten-Vertauschung). Nach dem Blick aufs Bild ist die Sache klar: Bei einem
formatfüllenden Quader vor Bodenebene ist die Tiefenverteilung eine völlig andere als
beim kleinen Kasten im Leeren — die Rangfolge **kann** nicht stimmen.

Zwei Lehren für die Aufträge, nicht für den Code:

1. **Ein Prompt, der Bauteile nennt, die die Geometrie nicht hat, ist eine Aufforderung
   zur Halluzination.** Material, Licht, Stimmung ja — Bauteile nein.
2. Der Bildbearbeitungs-Weg (§2) hält den Ausschnitt nicht von selbst. Ob ein echtes
   Depth-ControlNet-Backbone das besser hält, ist genau die Frage, die der
   Backbone-Vergleich beantworten muss — dieses Ergebnis ist der erste Referenzpunkt.

## 3a · Der Massstab: gemessene Umgebung

| Grösse | Wert |
|---|---|
| VRAM-Spitze des ganzen Laufs (Schichtauslagerung) | **2 862 MiB** |
| VRAM-Grundlast (Ollama entladen) | 1 071 MiB |
| Renderzeit (512², 28 Schritte) | 148–189 s |
| torch / torchvision | 2.11.0+cu128 / 0.26.0+cu128 |
| diffusers / transformers / accelerate | 0.39.0 / 5.15.0 / 1.14.0 |
| CUDA-Fassung des torch-Pakets | 12.8 |
| Blackwell-Warnung (sm_120) | geprüft: `sm_120` in `torch.cuda.get_arch_list()`, echter Kernel läuft |

## 4 · Zwei Fehler, die erst zusammen auffielen

**`tiefenschaetzer.standard_modell_wurzel` las die Umgebungsvariable nicht.** Sie rechnete
fest mit `/ai/modelle`, während `render.standard_modell_wurzel` `$AIIMAGING_MODELLE`
auswertet — obwohl ihr Docstring «dieselbe Konvention» behauptete. Folge auf einer
Maschine mit anderer Ablage: Der Render läuft 189 Sekunden durch, und **danach** scheitert
die Bewertung an einer Repo-Kennung. Also ausgerechnet der Teil, der das Ergebnis prüfen
soll, und erst dann, wenn der teure Teil bezahlt ist. Behoben, indem die Funktion jetzt
`render.standard_modell_wurzel` aufruft statt sie nachzubauen.

**Zwei Konventionen, die sich «dieselbe» nennen, sind schlimmer als zwei, die es offen
nicht sind.** Beim ersten liest man den Docstring und prüft nicht nach.

## 5 · Die Connector-Schicht am echten Bestand

40 echte IFC-Dateien aus laufenden Projekten, 201 MB, drei Erzeuger:

| Anzahl | Zeichenkette (wörtlich, aus FILE_NAME Feld 5 \| 6) | erkannt als |
|---|---|---|
| 28 | `IfcOpenShell 0.8.5-1c5b825 \| IfcOpenShell 0.8.5-1c5b825` | IfcOpenShell |
| 10 | `DDS_IFC v3.0 \| Graphisoft - Archicad - 28.4.0` | ArchiCAD |
| 2 | `ODA SDAI 24.3 \| Autodesk Revit 24.1.0.66 (ENG) - IFC 24.1.0.66` | Revit |

**40 von 40 erkannt, kein `herkunft: null`, kein `HerkunftError`.**

Der lehrreiche Teil steht in der mittleren Spalte: In zwei von drei Fällen trägt **Feld 5
einen fremden Namen** — DDS bzw. ODA sind die Exportbibliotheken, nicht die Programme. Nur
Feld 6 nennt den Erzeuger. Die Erkennung hält, weil **beide** Felder durchsucht werden;
sie hielte nicht, wenn Feld 5 Vorrang bekäme.

Einheiten: 25× `MILLI+METRE`, 15× `METRE`. Keine Umrechnungseinheit, kein Zoll.
Schemata: 30× IFC4, 10× IFC2X3 (alle ArchiCAD-Dateien sind IFC2X3).
`up_axis`: 40× `Z_UP`, 40× als `BELEGT` — wie ISO 16739 es verlangt.

### Zwei echte kaputte Exporte

Zwei Dateien erklären Millimeter und liefern 0,16 m bzw. 0,45 m — mit herausgerechnetem
Faktor wären es 160 m und 447 m. `pruefe_einheit_gegen_masse` benennt beide korrekt. Der
Fall ist also nicht theoretisch: **zwei von vierzig.**

### Und ein Fehlalarm, der Aufmerksamkeit verdient

Zwei weitere Dateien melden `stimmig=False` mit 1127 m und 1002 m grösster Kante. Das sind
Umgebungs- und Bestandsmodelle, keine Einzelbauten. Die Funktion sagt richtig, dass die
Einheit die Abweichung nicht erklärt — aber sie meldet einen Verdacht, wo keiner ist.
`MAX_GEBAEUDE_M` kennt nur den Begriff «Gebäude», und ein Städtebaukontext ist
regelmässig grösser. **Von den 36 stimmigen Modellen liegt die grösste Kante schon bei
795 m** — der Abstand zur Schranke ist dünn.

Empfehlung, nicht ausgeführt: Der Vergleich braucht einen zweiten Begriff neben «Gebäude»
(etwa «Kontext» oder «Areal»). Die Schranke gehört dem Torwächter mit, darum wurde sie
nicht angefasst.

### Zum Lesefenster

Fünf Dateien übersteigen die 2 MB (2,7 / 7,3 / 55,4 / 62,8 / 62,8 MB). **Alle fünf wurden
vollständig gedeutet**, alle setzten die Teilgelesen-Warnung, keine meldete fälschlich
«keine Einheit». `deute()` bleibt bei 0,016 s auch für die grösste Datei — das Fenster
wirkt. `ifc_zu_glb` schaffte alle 40 Konversionen, 5,76 Mio Dreiecke, längster Lauf 197 s.

## 6 · Eine Einschränkung, die dazugehört

Alle 40 Dateien stammen aus **einem** Büro und damit aus einer begrenzten
Werkzeuglandschaft. Dass Rhino, Vectorworks oder Allplan erkannt werden, ist damit
**nicht** belegt — nur, dass diese drei es werden. Der Ordner, der laut Auftrag die
Modelle tragen sollte, enthielt ausschliesslich zwei ArchiCAD-Projektdateien (`.pln`) und
damit nichts Deutbares; der ausgewertete Bestand stammt aus den Projektordnern desselben
Laufwerks.

## 7 · Änderungen an fremdem Code

Alle in `src/aiimaging/`, alle unter dem Mandat «bei weiterem Bruch direkt ändern», alle
mit der Auflage, keine Weiche an Versionsnummern zu hängen:

| Stelle | Was | Weiche prüft |
|---|---|---|
| `render._lege_auf_geraet` | drei Auslagerungsstufen statt `.to("cuda")` | freien VRAM **jetzt** (`mem_get_info`) gegen Summe **und** grösste Komponente |
| `render._vertraegliche_argumente` | übergibt nur, was die Pipeline annimmt | `inspect.signature(pipeline.__call__)` |
| `render._generator_geraet` | Seed-Gerät nicht aus `pipeline.device` | ob der gemeldete Gerätetyp `meta` ist |
| `render._pipeline_adapter` | Tiefenkarte als `image`, wenn kein `control_image` | Vorhandensein des Arguments |
| `render.rendere` | Adapter-Hinweise wandern ins Ergebnis | bestehender Wörterbuch-Rückgabeweg |
| `tiefenschaetzer.standard_modell_wurzel` | ruft `render.standard_modell_wurzel` | — |

Keine dieser Weichen liest eine Versions- oder Modellnummer. Testsuite vor und nach den
Änderungen identisch: **1503 grün, 4 rot**.

## 8 · Die vier roten Tests gehören nicht zu diesen Änderungen

`test_render.py::test_import_des_moduls_zieht_keinen_gpu_stack_nach`,
`test_render.py::test_lade_modell_scheitert_erst_am_fehlenden_torch`,
`test_stil_qa.py::test_stil_qa_laedt_keine_schweren_bibliotheken` und
`test_tiefenschaetzer.py::test_import_des_moduls_zieht_keinen_gpu_stack_nach`
schlagen **mit und ohne** die Änderungen identisch fehl (gegengeprüft per `git stash`).

Sie behaupten, ein Import ziehe `torch`/`diffusers` nicht nach — und prüfen das an
`sys.modules`. In einer venv, die den GPU-Stack **hat** und in der ein anderes Testmodul
ihn bereits geladen hat, kann diese Zusicherung nicht halten. Die Tests sind im
Entwicklungscontainer grün und auf der Maschine, die den Stack wirklich trägt, rot.

Das ist die schlechtere Richtung: Die Zusicherung ist dort unprüfbar, wo sie gebraucht
wird. Wer sie halten will, muss den Import in einem **frischen Interpreter** prüfen
(`subprocess.run([sys.executable, "-c", "import aiimaging.render, sys; ..."])`) — dann
gilt sie in beiden Umgebungen. Nicht geändert, weil es fremde Tests sind und die
Entscheidung dem Eigner gehört.
