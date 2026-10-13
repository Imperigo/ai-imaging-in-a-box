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

## Was im Bericht neu steht

| Feld | Bedeutung |
|---|---|
| `blickwinkel_quelle` | `"aufnahme"` oder `"ring"` |
| `aufnahme.auswahl` | Bilder und Augenblicke gesamt/gewählt, Kameras je Augenblick, Modelle |
| `aufnahme.gleichheit` | Median, P90 (absolut und relativ), Kameras im Bereich, Schwellen, Urteil |
| `aufnahme.grund` | warum die Aufnahme nicht benutzt wurde |
| `deckung.anteil` | Anteil der dichten Splat-Punkte höchstens 3 Voxel von einer Netzfläche |
| `netz.inseln` | Stücke gesamt, grösstes, entfernt, entfernter Anteil der Dreiecke |
| `voxel` | angefragt, benutzt, Versuche mit Blockzahl, Grund einer Vergrösserung |

## Probelauf ohne Grafikkarte (CPU-Ersatzrenderer, 13.10.2026)

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
3. Rendern mit `gsplat.rasterization(…, render_mode="RGB+ED")` — Farbe und erwartete Tiefe.
4. Verschmelzen mit Open3D (TSDF, 7-cm-Voxel, Blockwache), Inseln entfernen, bei Bedarf
   vereinfachen, Deckung zählen.
5. PLY mit Eckpunktfarben, im System des Splats (die Verortung wendet Blender an), dazu ein
   Bericht ohne Pfade.

Der Abholer ruft die Brücke **einmal je Auftrag**; dasselbe Netz kommt danach aus dem Speicher.

## Was am Heim-PC noch zu messen ist

* **Mit der Aufnahme** (`AIIMAGING_SPLAT_AUFNAHME` auf `sparse/0`): `blickwinkel_quelle`,
  `aufnahme.gleichheit` (erwartet Median ~0,25 % der Diagonale), `deckung.anteil` gegen den
  Ring, `netz.inseln`, ob die Blockwache anschlägt (`voxel`), Rechenzeit — und im Bild, ob die
  Fläche neben dem Bauwerk über 21–26 % steigt.

* Rechenzeit und Grafikspeicher an einem echten Splat (Vorgaben: 640 × 480, 16 Blickwinkel je
  Kreis = 48 Bilder, Voxel 7 cm).
* Ob das Netz das Konfetti beendet (dieselben Kameras wie `auf-20261008-274`).
* Ob Augenhöhe, Neigungen und Umlauf am Gehweg-Splat die Flächen fassen, oder ob Löcher bleiben.
