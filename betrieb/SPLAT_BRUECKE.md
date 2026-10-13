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
numpy, prüft, dass torch die Karte sieht, und rechnet zum Schluss einen synthetischen Splat
(`tools/make_test_splat.py`) mit echtem gsplat zu einem Netz. Es installiert nichts ausserhalb
von `.venv-splat`.

| Was | Vorgabe | Wann ändern |
|---|---|---|
| `PYTHON` | `python3.11` | Hier geprüft mit 3.11 (open3d 0.20). |
| `TORCH_INDEX` | `https://download.pytorch.org/whl/cu130` | Passend zur CUDA-Fassung des Treibers (`nvidia-smi`, Zeile «CUDA Version»). cu130 seit `auf-20261013-275`: cu124 kennt die RTX 5090 nicht. |
| `GSPLAT_VERSION` | `1.5.3` | Nur nach einem Messauftrag. |

Liegt die Umgebung woanders, zeigt `AIIMAGING_SPLAT_PYTHON` auf ihr Python; das Netz wird nach
Inhalt abgelegt in `AIIMAGING_SPLAT_NETZ_SPEICHER` (sonst `~/.cache/aiimaging/splat-netz`).

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
2. Blickwinkel: ein Ring auf Augenhöhe (1,6 m) im Zentrum der dichten Punkte, nach aussen, in zwei
   Neigungen; dazu eine Umlaufbahn von aussen nach innen (`aiimaging.kontext_netz`, alle Zahlen
   **GESETZT**).
3. Rendern mit `gsplat.rasterization(…, render_mode="RGB+ED")` — Farbe und erwartete Tiefe.
4. Verschmelzen mit Open3D (TSDF, 7-cm-Voxel), Inseln entfernen, bei Bedarf vereinfachen.
5. PLY mit Eckpunktfarben, im System des Splats (die Verortung wendet Blender an), dazu ein
   Bericht ohne Pfade.

Der Abholer ruft die Brücke **einmal je Auftrag**; dasselbe Netz kommt danach aus dem Speicher.

## Was am Heim-PC noch zu messen ist

* Rechenzeit und Grafikspeicher an einem echten Splat (Vorgaben: 640 × 480, 16 Blickwinkel je
  Kreis = 48 Bilder, Voxel 7 cm).
* Ob das Netz das Konfetti beendet (dieselben Kameras wie `auf-20261008-274`).
* Ob Augenhöhe, Neigungen und Umlauf am Gehweg-Splat die Flächen fassen, oder ob Löcher bleiben.
