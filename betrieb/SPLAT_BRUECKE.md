# Splat-Brücke — die Umgebung `.venv-splat` einrichten

**Warum das hier liegt.** Bis zum 13.10.2026 zeichnete Blender den Splat als harte Kugeln, und das
Bildmodell malte daraus «Konfetti» (`auf-20261008-271` bis `-274`). Owner-Entscheid 79: Der Splat
wird mit **gsplat** richtig gerendert und mit **Open3D** zu einem farbigen Netz verschmolzen; Blender
lädt das Netz wie ein gewöhnliches Objekt. Das braucht eine eigene Umgebung mit torch, gsplat und
open3d — **nie** im Produkt-venv (Regel 4).

**Ohne diese Umgebung läuft alles weiter wie bisher**, mit den Kugeln — und jedes Ergebnis sagt es
in `verdict.hinweise`: «UMGEBUNG ALS NOTLOESUNG (Kugeln) gezeichnet — Splat-Bruecke nicht
eingerichtet …». Der Vermerk `kontext.weg` steht dann auf `"kugeln"`, mit der Brücke auf `"netz"`.

## Einrichten (HomeStation)

    bash betrieb/splat-umgebung.sh

Das Skript legt `.venv-splat` im Repo an, installiert torch (CUDA), `gsplat==1.5.3`, open3d und
numpy, prüft, dass torch die Karte sieht, und rechnet zum Schluss einen synthetischen Strassenraum
(`tools/make_test_splat.py --form strasse`) mit echtem gsplat zu einem Netz — einmal mit dem Ring,
einmal mit den Kameras einer synthetischen Aufnahme (`tools/make_test_colmap.py --form strasse`).
Es installiert nichts ausserhalb von `.venv-splat`.

**Kein pycolmap.** Die COLMAP-Aufnahme liest der Runner mit eigenem Code
(`aiimaging/kontext_netz.py`, nur Standardbibliothek). pycolmap selbst ist BSD-3-Clause, aber das
Rad auf PyPI (4.2.1, am 13.10.2026 geprüft) bindet Teile von SuiteSparse unter **GPL-2.0+**
statisch ein (CHOLMOD Supernodal/MatrixOps, SPQR) — Regel 1 (siehe `NOTICE`).

| Was | Vorgabe | Wann ändern |
|---|---|---|
| `PYTHON` | `python3.11` | Hier geprüft mit 3.11 (open3d 0.20). |
| `TORCH_INDEX` | `https://download.pytorch.org/whl/cu130` | Passend zur CUDA-Fassung des Treibers (`nvidia-smi`, Zeile «CUDA Version»). cu130 seit `auf-20261013-275`: cu124 kennt die RTX 5090 nicht. |
| `GSPLAT_VERSION` | `1.5.3` | Nur nach einem Messauftrag. |

Liegt die Umgebung woanders, zeigt `AIIMAGING_SPLAT_PYTHON` auf ihr Python; das Netz wird nach
Inhalt abgelegt in `AIIMAGING_SPLAT_NETZ_SPEICHER` (sonst `~/.cache/aiimaging/splat-netz`).

## Die Aufnahme: woher die Blickwinkel kommen (seit 13.10.2026)

**Anlass:** `auf-20261013-275` — mit gesetzten Blickwinkeln (Ring in der Mitte, Umlauf) deckte das
Netz am echten Splat nur 21–26 % der Fläche neben dem Bauwerk, in Fetzen (42 % der Dreiecke fielen
als Inseln weg). Ein Splat ist nur aus den Richtungen verlässlich, aus denen er gelernt wurde.
Darum rendert die Brücke, wo es sie gibt, **aus den Kameras der COLMAP-Aufnahme**.

Woher der Ordner kommt — der Vertrag (`RenderScene.context`) hat dafür **kein Feld**; bis das
entschieden ist, gilt eine Konvention, in dieser Reihenfolge:

1. ausdrücklich: `seams.splat_zu_netz(…, aufnahme=…)` / `kontext_vorbereiten(…, aufnahme=…)`;
2. `AIIMAGING_SPLAT_AUFNAHME` — für die HomeStation und den Dienst, z. B. auf `…/sparse/0`;
3. neben dem Splat: `<ordner>/sparse/0`, `<ordner>/../sparse/0` oder `<stamm>.colmap/`.

Ein Ordner gilt, wenn darin `images.bin`/`.txt` **und** `cameras.bin`/`.txt` liegen (COLMAP 3
oder 4, mit oder ohne Rig). Der Vermerk sagt ohne Pfad, was galt
(`aufnahme: "parameter" | "umgebung" | "neben dem splat" | "keine"`), und der Inhalt von
`cameras`/`images`/`frames`/`rigs` steht im Speicherschlüssel: Andere Kameras ergeben ein
anderes Netz.

**Die Gleichheitsprüfung**, bevor eine Kamera benutzt wird: Median und 90-%-Perzentil des
Abstands der COLMAP-Punkte zur nächsten dichten Splat-Mitte, als Anteil der Diagonale des
dichten Bereichs (höchstens 1 % bzw. 4 %), und mindestens die Hälfte der Kamerazentren im
Bereich des Splats (um ein Viertel erweitert). Alles relativ, weil die Splat-Einheiten keine
Meter sind. Am echten Splat mass die HomeStation 0,25 % (Median) — klar darunter. Fällt die
Prüfung durch, rechnet die Brücke mit dem Ring und schreibt den Grund in den Bericht
(`aufnahme.grund`); der Vermerk trägt ihn als `aufnahme_grund`.

Gewählt werden höchstens **240 Bilder** (`AUFNAHME_BLICKE_MAX`), gleichmässig über die
Augenblicke, jeweils **alle Kameras des Rigs**; die Brennweite wird auf die Renderbreite
skaliert, das Seitenverhältnis bleibt das der Aufnahme (am echten Splat 1086 × 1086 → 640 × 640).
Fischaugen und Panoramen werden ausgelassen und gezählt.

## Die Blockwache

Open3D 0.20 stürzte am echten Splat bei 5-cm-Voxeln in `extract_triangle_mesh` ab (~435 000
aktive Blöcke; 324 000 stürzt, 245 000 geht). Mit den Kameras der Aufnahme sieht die Brücke mehr
Fläche, die Blockzahl steigt. Darum zählt sie beim Verschmelzen nach jedem Bild; über
`BLOECKE_MAX` (250 000) beginnt sie mit grösserem Voxel neu (höchstens viermal) und schreibt es
in den Bericht (`voxel.vergroessert`, `voxel.versuche`, `voxel.grund`). Zum Messen der Grenze:
`--bloecke-max N` am Runner.

## Der Tiefenfilter (seit 13.10.2026, nach `auf-20261013-276`)

**Anlass:** Am echten Splat stimmten die Posen der Aufnahme (gsplat aus den Aufnahmekameras ergab
die Aufnahmebilder deckungsgleich), aber die erwartete Tiefe war stark gesprenkelt, und die gefilmte
Person samt Arm stand als Wolke nah vor den Kameras. Die TSDF machte daraus 497 497 Stücke, 69 % der
Dreiecke fielen als Inseln weg, die Deckung blieb bei 10 %. Seither siebt der Runner jedes
Tiefenbild, bevor es verschmolzen wird; ein verworfener Bildpunkt bekommt Tiefe 0.

| Filter | verwirft einen Bildpunkt, wenn … | Schwelle (GESETZT) |
|---|---|---|
| `deckkraft` | die akkumulierte Deckkraft (alpha aus gsplat) unter der Schwelle liegt | `DECKKRAFT_TIEFE` 0,7 |
| `sprenkel` | die Tiefe vom Median ihrer 3 × 3 Nachbarn um mehr als den Anteil abweicht | `TIEFE_SPRUNG_REL` 5 % |
| `streuung` | die Tiefen entlang des Strahls um mehr als den Anteil der Tiefe streuen | `TIEFE_STREUUNG_REL` 10 % |
| `nah` | die Tiefe unter der Mindestentfernung liegt (Meter der Welt, über den Massstab) | `NAH_MIN_M` 1,5 m |
| `weg` | der Punkt näher als dies an **irgendeiner** Kamera der Aufnahme liegt | `WEG_MIN_M` 1,2 m (geprüft bis 10 m) |
| `maske` | die Maske der Aufnahme ihn ausblendet | Grauwert 128 |

* **Warum nicht «D / alpha gegen ED»:** gsplat 1.5.3 rechnet ED genau so; der Vergleich prüft
  nichts. Die zweite Schätzung entlang des Strahls ist die **Streuung**: Ein zweiter Durchgang von
  gsplat mischt statt der Farbe `z` und `z²` je Kamera (`colors` der Form `[C, N, 2]`,
  `sh_degree=None`) → `E[z²] − E[z]²`. **Nur am Heim-PC prüfbar** (CUDA). Scheitert dieser
  Durchgang, setzt der Filter aus und der Bericht sagt es (`tiefenfilter.streuung_fehler`); die
  Brücke bricht daran nicht ab.
* **Warum `weg`:** Am synthetischen Strassenraum nahmen Nahbereich und Masken nur die Person
  **dieses** Augenblicks weg. Der Raum, durch den die Kamera getragen wurde, ist leer — ausser
  dem, der sie trug. 1,2 m statt 1,5 m, damit die Kugel um eine Kamera auf Brusthöhe den Boden
  nicht berührt. Wirkt nur mit Blickwinkeln aus der Aufnahme (`tiefenfilter.weg_aktiv`).
* **Vergleichsläufe:** `seams.splat_zu_netz(…, tiefenfilter="keine")` oder eine Auswahl wie
  `"streuung,nah,weg"`; am Runner `--tiefenfilter=…`. Die Auswahl steht im Speicherschlüssel.

## Die Masken der Aufnahme

**Nur neben derselben Aufnahme** (Auskunft der HomeStation, 13.10.2026): Masken gehören zu einem
Lauf mit eigenem `sparse/0` und eigenem Splat. **Der Abnahme-Splat aus 271–276 hat keine** — die
Masken dort gehören zu einem anderen Lauf. Eine Übertragung zwischen Läufen per Name gibt es
nicht, weil deren Posen nicht als gleich geprüft sind. Darum muss der Tiefenfilter auch ohne
Masken tragen; die Masken sind ein Zusatz.

* **Wo:** relativ zu `sparse/0` in `../../masks` (so bei der HomeStation:
  `<lauf>/masks/<ansicht>/`), dann `../masks`, dann `masks/`; ausdrücklich über
  `seams.splat_zu_netz(…, masken=…)` oder `AIIMAGING_SPLAT_MASKEN`.
* **Name:** voller Bildname aus `images.bin` plus `.png` (`back/0031.jpg` →
  `masks/back/0031.jpg.png`), sonst derselbe Name, sonst Stamm plus `.png`.
* **Polarität:** aus `maske.json` (im Maskenordner oder darüber), wenn sie es sagt — ein Feld
  `polaritaet`/`polarity`, sonst das Schema `kosmoprepare.splat-maske/…` als «weiss = behalten».
  Ohne `maske.json` gilt **weiss = behalten** (Vorgabe); ist dann über alle benutzten Masken
  weniger als die Hälfte weiss, gilt die Mehrheitsregel (schwarz = behalten) mit Warnung.
* **Lesen:** mit Open3D (`o3d.io.read_image`), keine neue Abhängigkeit; auf die Renderbreite
  (640) nach dem nächsten Nachbarn skaliert.
* **Im Speicherschlüssel:** sha256 über Namen und Inhalt aller gefundenen Masken und `maske.json`.
* **Im Bericht** (`masken`): `gefunden`, `anzahl`, `benutzt`, `angewandt`, `lage` (ohne Pfad),
  `polaritaet`, `polaritaet_quelle` (`maske.json` | `vorgabe` | `mehrheitsregel`), `weiss_anteil`,
  `warnung`.

## Vier Fehler aus `auf-20261013-276`, behoben

1. **Aufnahme hinter einem Verweis (Symlink):** gesucht wird neben dem Pfad, wie er kommt, und
   danach neben seinem Ziel (`kontext_netz.aufnahme_kandidaten`, ebenso die Masken).
2. **Zeiten:** Jeder Voxelversuch steht mit `dauer_s` in `voxel.versuche`; dazu
   `zeiten_s.bibliotheken_s` (torch, gsplat, Open3D laden), `blockwache_verworfen_s` und
   `ungezaehlt_s` (was keine Teilzeit erklärt).
3. **Netz-sha256 nicht reproduzierbar:** Ursache Open3D, nicht gsplat — die Hashtabelle der
   `VoxelBlockGrid` füllt sich parallel, die Dreiecke kamen in wechselnder Reihenfolge (hier
   nachgestellt: drei Läufe, drei sha256, nach Lage sortiert dieselben Ecken). Das Netz wird vor
   dem Vereinfachen und Schreiben nach Lage geordnet; gleicher Schlüssel → bitgleiche Datei (am
   Ersatzrenderer geprüft; ob gsplat auf der Karte bitgleich rendert, ist am Heim-PC zu sehen).
   Geschadet hatte es nicht: Der Speicherschlüssel hängt am Inhalt des Splats und den Parametern,
   die Kette am Inhalt des Splats; die Netz-sha256 prüft nur, dass das abgelegte Netz das des
   eigenen Berichts ist.
4. **Deckung:** eine Zufallsstichprobe (fester Startwert) von bis zu 200 000 über **alle** dichten
   Punkte; `deckung.dicht_gesamt` sagt, aus wie vielen.

## Was im Bericht neu steht

| Feld | Bedeutung |
|---|---|
| `blickwinkel_quelle` | `"aufnahme"` oder `"ring"` |
| `aufnahme.auswahl` | Bilder und Augenblicke gesamt/gewählt, Kameras je Augenblick, Modelle |
| `aufnahme.gleichheit` | Median, P90 (absolut und relativ), Kameras im Bereich, Schwellen, Urteil |
| `aufnahme.grund` | warum die Aufnahme nicht benutzt wurde |
| `deckung.anteil` | Anteil der dichten Splat-Punkte höchstens 3 Voxel von einer Netzfläche |
| `netz.inseln` | Stücke gesamt, grösstes, entfernt, entfernter Anteil der Dreiecke |
| `voxel` | angefragt, benutzt, Versuche mit Blockzahl und Dauer, Grund einer Vergrösserung |
| `tiefenfilter` | eingeschaltete Filter, je Filter der Anteil verworfener Bildpunkte mit Tiefe, gesamt, Schwellen, `weg_aktiv`, `streuung_bilder`/`streuung_fehler` |
| `masken` | gefunden, Zahl, benutzt, angewandt, Lage, Polarität und ihre Quelle, Warnung |
| `zeiten_s` | Teilzeiten samt `bibliotheken_s`, `blockwache_verworfen_s`, `ungezaehlt_s` |

## Probelauf ohne Grafikkarte (CPU-Ersatzrenderer, 13.10.2026)

**Nachtrag Tiefenfilter:** Die Probe mit der gefilmten Person (Strassenraum, Voxel 7 cm) steht in
`docs/SPLAT_TIEFENFILTER_2026-10-13.md`: ohne Filter 8 989 Netzstücke, mit Streuung 762, mit allen
Filtern 860; Nahbereich und Masken allein kaum besser (8 827 / 7 255). Die Tabelle unten stammt von
**vor** dem Tiefenfilter und vor der erwarteten Tiefe im Ersatzrenderer; mit beiden deckt der Ring
am Strassenraum noch 56 %, die Aufnahme 96 % (151 statt 75 Stücke).

Synthetischer Strassenraum (`--form strasse`, 12 000 Punkte, 12 × 75 m), Voxel 0,15 m,
Renderbreite 160 Bildpunkte, Aufnahme mit 80 Augenblicken × 4 Kameras. **Nur Probe** — gsplat
rendert anders, die Zahlen sagen etwas über die Wege, nicht über das echte Netz.

| | Ring + Umlauf | Aufnahme |
|---|---|---|
| Blickwinkel | 24 | 240 (60 Augenblicke × 4) |
| Deckung | 70,6 % | 96,0 % |
| Netzstücke vor dem Aufräumen | 2547 | 75 |
| als Inseln entfernt | 7,9 % der Dreiecke | 0,35 % |
| Dreiecke | 309 621 | 269 530 |
| Zeit gesamt | 6,5 s | 50 s (davon ~40 s Ersatzrenderer) |

Gegenprobe: dieselbe Aufnahme um 10 m schräg verschoben → Median 6,7 % der Diagonale, Ring mit
Grund. Am kompakten Platz (`--form platz`) deckt der Ring dagegen besser (97,7 %) als ein
Kreisweg der Aufnahme (84,6 %): Die Aufnahme sieht nur, was sie sah.

**Ersatzrenderer korrigiert (13.10.2026):** Er trug bis dahin je Quadrat die Tiefe der Mitte;
bei flachem Blick hob das den Boden im Netz um ~3 Voxel an (Wand doppelt). Jetzt schneidet jeder
Bildpunkt die Scheibe des Gaussians. Die TSDF allein legt eine Ebene exakt (geprüft).

### gsplat ohne Kompilieren

`gsplat` kompiliert seine CUDA-Kerne beim ersten Rendern. Dafür braucht es das CUDA-Toolkit
(`nvcc`) in derselben Fassung wie torch; der erste Lauf dauert dann einige Minuten. Wer das nicht
will, nimmt ein vorkompiliertes Rad von gsplat (Index je torch-/CUDA-Fassung, siehe
<https://github.com/nerfstudio-project/gsplat>, Abschnitt Installation) und setzt die Fassung
gleich.

## Was die Brücke rechnet

`aiimaging.seams.splat_zu_netz(ply, matrix=…)` startet
`src/aiimaging/runners/splat_zu_netz_runner.py` im `.venv-splat`:

1. Gaussians lesen (Lage, Skala, Drehung, Deckkraft, Farbe bis SH-Grad 3).
2. Blickwinkel: aus den Kameras der Aufnahme, wenn sie da ist und zum Splat passt (oben).
   Sonst ein Ring auf Augenhöhe (1,6 m) im Zentrum der dichten Punkte, nach aussen, in zwei
   Neigungen, und eine Umlaufbahn von aussen nach innen (`aiimaging.kontext_netz`, alle Zahlen
   **GESETZT**).
3. Rendern mit `gsplat.rasterization(…, render_mode="RGB+ED")` — Farbe, erwartete Tiefe und
   akkumulierte Deckkraft; ein zweiter Durchgang für die Streuung entlang des Strahls.
   Danach der Tiefenfilter (oben).
4. Verschmelzen mit Open3D (TSDF, 7-cm-Voxel, Blockwache), Inseln entfernen, bei Bedarf
   vereinfachen, Deckung zählen.
5. PLY mit Eckpunktfarben, im System des Splats (die Verortung wendet Blender an), dazu ein
   Bericht ohne Pfade.

Der Abholer ruft die Brücke **einmal je Auftrag**; dasselbe Netz kommt danach aus dem Speicher.

## Was am Heim-PC noch zu messen ist

* **Der Tiefenfilter am Abnahme-Splat** (ohne Masken — er hat keine): drei Läufe,
  `tiefenfilter="keine"`, `"streuung,nah,weg"` und alle; je Lauf `netz.inseln`, `deckung`,
  `tiefenfilter.je_filter` und im Bild die Fläche neben dem Bauwerk. Läuft der zweite
  gsplat-Durchgang (`tiefenfilter.streuung_bilder` = Zahl der Blickwinkel, kein
  `streuung_fehler`)? Kostet `deckkraft` am trainierten Splat ebenso Fläche wie am synthetischen?
* **Mit Masken** am Lauf, zu dem sie gehören (eigener Splat, eigenes `sparse/0`): `masken.gefunden`,
  `polaritaet_quelle` = `maske.json`, `je_filter.maske`.
* Ist das Netz auch mit gsplat auf der Karte bei gleichem Schlüssel bitgleich?

* **Mit der Aufnahme** (`AIIMAGING_SPLAT_AUFNAHME` auf `sparse/0`): `blickwinkel_quelle`,
  `aufnahme.gleichheit` (erwartet Median ~0,25 % der Diagonale), `deckung.anteil` gegen den
  Ring, `netz.inseln`, ob die Blockwache anschlägt (`voxel`), Rechenzeit — und im Bild, ob die
  Fläche neben dem Bauwerk über 21–26 % steigt.

* Rechenzeit und Grafikspeicher an einem echten Splat (Vorgaben: 640 × 480, 16 Blickwinkel je
  Kreis = 48 Bilder, Voxel 7 cm).
* Ob das Netz das Konfetti beendet (dieselben Kameras wie `auf-20261008-274`).
* Ob Augenhöhe, Neigungen und Umlauf am Gehweg-Splat die Flächen fassen, oder ob Löcher bleiben.
