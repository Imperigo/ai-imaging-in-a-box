# BEFUND 2026-09-06 — Blender rechnet auf der CPU, gemessen statt geschaetzt

**Stand 06.09.2026:** offen — Kommentar widerlegt (CPU ist auf dieser Maschine im vollen realistischen Sample-/Aufloesungsbereich sogar SCHNELLER als GPU, nicht "keine GPU vorhanden"), aber Code bewusst nicht geaendert, wie beauftragt.

**An:** Owner · **Von:** Home-PC-Worker (HomeStation, RTX 5090) · 06.09.2026
**Vorgang:** Messauftrag dieser Sitzung — CPU-vs-GPU-Vergleich fuer `blender_depth_stage.py`, Code bewusst NICHT angefasst.

---

## 1 · Die Stelle, woertlich

**Datei:** `src/aiimaging/runners/blender_depth_stage.py:1237`, Funktion `_renderparameter_setzen`:

```python
szene.cycles.samples = a.samples
szene.cycles.device = "CPU"                          # in dieser Umgebung gibt es keine GPU
```

**Der Kommentar nennt eine Begruendung, und sie ist an einer anderen Stelle im selben Repo bereits selbst widerlegt.** `auftraege/ergebnisse/auf-20260820-19.json` (Urteil, Feld `abweichung_vom_auftrag_und_warum`) haelt am 20.08.2026 wortgleich fest: *„blender_depth_stage.py setzt in Zeile 744 `szene.cycles.device = \"CPU\"` fest verdrahtet, mit dem Kommentar «in dieser Umgebung gibt es keine GPU», und hat dafuer keinen Schalter."* Die Zeilennummer hat sich seither verschoben (744 → 1237, das Skript ist seither gewachsen), der Wortlaut des Kommentars nicht. **Die Begruendung galt fuer den Container, in dem dieses Projekt entwickelt wird** (vgl. `src/aiimaging/auftrag.py:5`: „Der Container, in dem entwickelt wird, hat keine GPU und keine Modellgewichte") — **nicht fuer die HomeStation**, auf der der Runner tatsaechlich ausgefuehrt wird. Dort steckt eine RTX 5090, von Blender selbst erkannt (s. §2). Die Begruendung gilt an dieser Stelle also nicht mehr.

## 2 · Miss statt schaetzen — drei Konfigurationen, `n=3` je Seite

**Aendere den Code NICHT** wurde eingehalten: Die Repo-Datei ist unangetastet (`git status` im Repo zeigt keine Aenderung an `blender_depth_stage.py`). Fuer die GPU-Seite lief eine **Kopie ausserhalb des Repos** (Scratch-Verzeichnis, kein Pfad mit Benutzernamen unten verwendet), in der **einzig** die device-Zeile ersetzt ist durch:

```python
_prefs = bpy.context.preferences.addons["cycles"].preferences
_prefs.compute_device_type = "OPTIX"
_prefs.get_devices()
for _dev in _prefs.devices:
    _dev.use = (_dev.type == "OPTIX")
szene.cycles.device = "GPU"
```

Aufgerufen wurde **dieselbe** Funktion, die auch die Produktion aufruft: `seams.baue_kommando_multipass()`/`seams._multipass_argumente()` unveraendert aus `src/aiimaging/seams.py`, nur der `--python`-Pfad zeigt auf die Kopie statt auf die Repo-Datei. Kommando (Muster, `<RUNNER>` = Repo-Datei bzw. Kopie):

```bash
blender --background --factory-startup --python <RUNNER> -- \
  --glb <testszene.glb> --out <out_dir> --aufloesung 512 --samples <N>
```

`blender` = `/snap/bin/blender`, **Blender 5.2.1 LTS**, aufgeloest ueber `seams.finde_blender()` (unveraendert). Ausgefuehrt ueber `subprocess.run(..., capture_output=True)`, **nicht** ueber Shell-Umleitung (`>` datei) — Letzteres scheitert auf dieser Maschine grundsaetzlich am AppArmor-Profil von `snap-confine` (`file_inherit` DENIED, jede Zieldatei, auch unter `$HOME`; Gegenprobe mit `journalctl -k`, siehe §5) — **derselbe Befund, den `auf-20260820-18.json` bereits fuer Dateiumleitung dokumentiert.** `subprocess`-Pipes sind davon nicht betroffen und liefern zuverlaessig; das ist der Weg, den `seams.py` in der Produktion ohnehin schon verwendet.

**Testszene:** synthetisch, per `tools/make_test_glb.py`/`baue_glb()` erzeugt (Regel 3 — keine echten Projektdaten). Zwei Groessen: die Standard-Testszene (2 Quader, 24 Dreiecke) und eine selbst zusammengesetzte, ebenfalls rein synthetische „Gebaeude"-Szene (Bodenplatte + Wandgitter, 73 Objekte, 876 Dreiecke) fuer eine realistischere Groessenordnung.

**Samples:** 16 ist der Vorgabewert an ZWEI Stellen im Produktcode (`seams.py:610` und `kette.py:217`) — kein Sonderfall. Reale Auftraege im Repo liegen zwischen 8 und 128 (`grep '"samples"' auftraege/*/*.json`), 512×512 ist die haeufigste Aufloesung. Alle drei gemessenen Konfigurationen liegen damit im tatsaechlich genutzten Bereich — **nicht** im kuenstlich aufgeblasenen Bereich von `auf-20260820-18/19` (dort 220 000 Samples, ausdruecklich um ueberhaupt eine minutenlange Laufzeit zu erzwingen).

### Konfiguration A — Vorgabewert (512×512, 16 Samples, kleine Testszene)

```
CPU:  1.769 s · 1.818 s · 1.820 s     Spanne 1.769–1.820 s (0.051 s)
GPU:  2.283 s · 2.331 s · 2.396 s     Spanne 2.283–2.396 s (0.113 s)
```
**GPU langsamer**, um 0.463–0.627 s (+25 % bis +35 % Wandzeit).

### Konfiguration B — 512×512, 128 Samples (oberes Ende des real genutzten Bereichs), kleine Testszene

```
CPU:  1.964 s · 1.965 s · 1.979 s     Spanne 1.964–1.979 s (0.015 s)
GPU:  2.313 s · 2.324 s · 2.338 s     Spanne 2.313–2.338 s (0.025 s)
```
**GPU langsamer**, um 0.334–0.374 s (+17 % bis +19 %).

### Konfiguration C — 512×512, 128 Samples, groessere synthetische Szene (73 Objekte, 876 Dreiecke)

```
CPU:  2.134 s · 2.173 s · 2.191 s     Spanne 2.134–2.191 s (0.057 s)
GPU:  2.416 s · 2.463 s · 2.487 s     Spanne 2.416–2.487 s (0.071 s)
```
**GPU langsamer**, um 0.225–0.353 s (+10 % bis +17 %).

**In allen drei gemessenen Konfigurationen ist die GPU langsamer, nicht schneller — durchgehend, ueber alle 18 Einzellaeufe (3 Konfigurationen × 2 Seiten × n=3), keine Ueberschneidung der Spannen.** Grund (mit `nvidia-smi` waehrend eines separaten, staerker belasteten Testlaufs bestaetigt — s. §4): Der GPU-Pfad zahlt bei jedem Blender-Start einen festen OptiX-Initialisierungsaufwand (Geraeteerkennung, Kernel-Kompilierung, Szenen-Upload), der bei diesen kurzen Laeufen (1,8–2,5 s gesamt) einen groesseren Anteil der Zeit ausmacht als die eigentliche Rechenzeit einspart. Die historische Messung `auf-20260820-18.json` zeigt konsistent dazu: Auf dieser Karte braucht dieselbe Szene bei 3000 Samples **2,2 s reine Rechenzeit auf der GPU** gegen 190 s auf der CPU — die GPU IST massiv schneller **an reiner Rechenzeit**, sobald diese lang genug ist, um den Fixkostenanteil zu ueberwiegen. Bei den hier tatsaechlich verwendeten 8–128 Samples ist die Szene aber so klein, dass die Rechenzeit selbst nur einen Bruchteil einer Sekunde betraegt und der Fixkostenanteil dominiert.

**Nebenbefund/Grenze dieser Messung:** Getestet wurde bis 876 Dreiecke, synthetisch (Regel 3 verbietet echte Projektdaten). Eine echte, deutlich komplexere Bauwerksgeometrie (mehr Objekte, mehr Materialien, mehr Kamerastrahlen an Kanten) koennte die Fixkosten der GPU eher amortisieren — dieser Kipppunkt wurde NICHT gemessen und ist damit nicht belegt, weder in die eine noch die andere Richtung.

## 3 · Ergebnisgleichheit — nicht byte-identisch, aber nicht durch Zufall verschieden

**SHA-256 der PNG/EXR-Dateien war in KEINEM Fall gleich** — nicht einmal zwischen zwei CPU-Laeufen derselben Konfiguration. Das ist ein Formatbefund, kein Renderbefund: Blender schreibt vermutlich laufzeitabhaengige Metadaten (Zeitstempel o.ae.) mit in die Dateien. **Pixelinhalt (per PIL/`numpy`, RGBA-Array, `|CPU − GPU|` je Kanal) zeigt ein anderes Bild:**

```
CPU-Lauf1 gegen CPU-Lauf2 (Basisrauschen, dieselbe Konfiguration):
  material_id.png:  max=0   mean=0.0        — pixelgenau identisch, alle drei Konfigurationen
  beauty_.png:       max=0   mean=0.0        — pixelgenau identisch, alle drei Konfigurationen

CPU-Lauf1 gegen GPU-Lauf1:
  Konfiguration A (16 Spl, klein):    material_id max=0 mean=0.0      · beauty max=1/255, 24 von 262144 Px betroffen
  Konfiguration B (128 Spl, klein):   material_id max=0 mean=0.0      · beauty max=1/255, 85 von 262144 Px betroffen
  Konfiguration C (128 Spl, gross):   material_id max=217/255, 28 Px  · beauty max=70/255, 11821 von 262144 Px (4,5 %)
```

**Einordnung:** Bei der kleinen Testszene sind CPU- und GPU-Bild praktisch deckungsgleich (hoechstens ±1 von 255 auf einer Handvoll Pixel — Rundungsartefakt, keine erkennbare Struktur). Bei der groesseren, kantenreicheren Szene treten sichtbare, aber lokal begrenzte Abweichungen an Objektkanten auf (die material_id-Abweichung von 217 betrifft nur 28 von 262 144 Pixeln — Silhouettenkanten, wo CPU- und OptiX-Ray-Traversierung bei Sub-Pixel-Grenzfaellen unterschiedliche Primaerstrahl-Treffer werten). **Das ist kein Absturz und keine grobe Fehlfarbe, aber auch keine Bit-Identitaet** — bei einer ID-Maske, die nachgelagert exakt ausgewertet wird, koennte das an genau diesen Kantenpixeln eine falsche ID liefern.

**Die Berichtsfelder** (`blender-report.json`: `bbox`, `bbox_size_m`, `sonne`, `deckungsgrad`, `n_meshes`, `material_id_tabelle`, `samples`, `aufloesung`) **sind in allen drei Konfigurationen zwischen CPU und GPU identisch** — das sind reine Geometrie-/Szenenwerte, unabhaengig vom Rechengeraet, wie erwartet.

**Nicht geprueft:** die Tiefenkarte (`tiefe_*.exr`) auf Pixelebene — in dieser Umgebung ist keine OpenEXR-Python-Bibliothek installiert (`import OpenEXR`/`cv2`/`imageio` schlagen alle fehl). Byte-Groesse ist in allen 18 Laeufen identisch (1 057 433 Byte), was auf gleiche Kanalstruktur/Aufloesung hindeutet, aber keine Pixelaussage ist.

## 4 · Gegenprobe: rechnet die GPU-Kopie ueberhaupt auf der Karte?

Damit ein „GPU ist langsamer"-Befund nicht auf einem still fehlgeschlagenen GPU-Umschalten beruht (die Probe muss widersprechen KOENNEN): `bpy.context.preferences.addons["cycles"].preferences.devices` zeigt auf dieser Maschine

```
NVIDIA GeForce RTX 5090   CUDA    verfuegbar
AMD Ryzen 9 9950X 16-Core  CPU     verfuegbar
NVIDIA GeForce RTX 5090   OPTIX   verfuegbar, von der Kopie aktiviert
```

Bei einem separaten, staerker belasteten Kontrolllauf (1024×1024, 20 000 Samples, selbe Kopie) sprang `nvidia-smi` waehrend des Laufs sekundengenau von **20 W/631 MiB (Leerlauf) auf 52–83 W/4338 MiB** und danach wieder zurueck — die Karte rechnet nachweislich mit, nicht nur dem Namen nach.

## 5 · Snap-Nebenbefund (Umfeld, nicht Auftrag)

`snap list blender` → 5.2.1, Revision 7740, „classic". `/snap/bin/blender > datei 2>&1` liefert **immer** Exit 0 und eine LEERE Datei — `journalctl -k` zeigt dazu durchgehend `apparmor="DENIED" operation="file_inherit" ... profile="/usr/lib/snapd/snap-confine"` fuer JEDE Zieldatei (getestet unter `/tmp`, unter `$HOME`, unter dem Scratch-Verzeichnis). `subprocess.run(cmd, capture_output=True)` (Pipe statt Datei) ist davon nicht betroffen und lieferte in allen 18+ Laeufen sauber Exit 0 mit Inhalt. Deckt sich mit `auf-20260820-18.json` (dort dieselbe Falle bereits fuer den direkten Blender-Aufruf dokumentiert). Kein Code geaendert, nur gemeldet.

## 6 · Ergebnis und Empfehlung

**Nicht getan, wie beauftragt:** Der Code in `src/aiimaging/runners/blender_depth_stage.py` ist unveraendert. Kein `git diff`, keine Aenderung im Repo.

**Die Messung selbst spricht klar gegen ein Umstellen auf GPU** — jedenfalls fuer die aktuelle Betriebsgroesse (8–128 Samples, ≤512 px, Szenen im drei- bis vierstelligen Dreiecksbereich): Die GPU ist in JEDER gemessenen Konfiguration langsamer (10–35 % mehr Wandzeit), und bei mehr Geometrie treten kleine, aber messbare Pixelabweichungen an Kanten auf, die CPU-CPU-Wiederholungen nicht zeigen. **Ein Umstieg brächte hier weder Geschwindigkeit noch Bild-Identität — er wäre ein Rückschritt auf beiden Achsen.**

**Trotzdem ist der Kommentar falsch** — er behauptet einen Tatbestand („keine GPU"), der auf dieser Maschine nicht zutrifft, auch wenn die Schlussfolgerung (CPU verwenden) die richtige bleibt. Empfehlung, nicht ausgefuehrt: den Kommentar an Zeile 1237 von einer falschen Tatsachenbehauptung auf den tatsaechlichen, jetzt gemessenen Grund umschreiben (etwa: „auf dieser Maschine langsamer als CPU bei den hier ueblichen Sample-/Aufloesungsgroessen — gemessen 06.09.2026, s. `BEFUND-2026-09-06-blender-rechnet-auf-cpu.md`"), **nicht** auf „keine GPU vorhanden".

## 7 · Abweichung von den Zahlen im Auftrag dieser Sitzung

- Es wurden **drei** Konfigurationen statt einer gemessen (Vorgabewert plus zwei Kontrollen), weil der Vorgabewert allein (16 Samples) eine sehr kurze, durch Fixkosten dominierte Messung ist und die Frage „gilt das auch bei mehr Last/mehr Geometrie" sonst offen bliebe.
- Es gibt **kein OpenEXR-Leseprogramm** in dieser Umgebung — die Tiefenkarte wurde nur ueber Dateigroesse verglichen, nicht pixelweise (s. §3).
- Alle Zeitmessungen sind Wanduhrzeit fuer den **gesamten Blender-Prozess** (inkl. Start, Import, beide Renderdurchgaenge, Report-Schreiben), nicht nur die reine Cycles-Renderzeit — das ist die fuer den Auftrag („derselbe Multipass-Lauf") relevante Grösse, aber es lohnt sich, das explizit zu nennen, damit niemand die Zahlen gegen eine reine Sample-Zeit haelt.
