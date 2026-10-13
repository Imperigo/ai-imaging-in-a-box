#!/usr/bin/env bash
# Legt die Umgebung `.venv-splat` fuer die Splat-Bruecke an (Owner-Entscheid 79, 13.10.2026).
#
# WARUM EIN EIGENES VENV: gsplat (Apache-2.0), Open3D (MIT) und PyTorch (BSD-3) sind
# permissiv, aber schwer — torch zieht die CUDA-Laufzeit nach, gsplat rendert nur mit
# CUDA. Regel 4: nichts davon im Produkt-venv. Aufgerufen wird nur
# `src/aiimaging/runners/splat_zu_netz_runner.py`, als Subprozess, ueber
# `aiimaging.seams.splat_zu_netz`. Anleitung und Hintergrund: betrieb/SPLAT_BRUECKE.md.
#
# Aufruf (im Repo-Wurzelverzeichnis, auf der HomeStation):
#     bash betrieb/splat-umgebung.sh
# Anpassbar ueber Umgebungsvariablen:
#     PYTHON=python3.11                               welcher Interpreter das venv bekommt
#     TORCH_INDEX=https://download.pytorch.org/whl/cu124   passend zum Treiber (nvidia-smi)
#     GSPLAT_VERSION=1.5.3
#
# Das Skript installiert NICHTS ausserhalb von `.venv-splat` und aendert keine Systemdateien.
set -euo pipefail

WURZEL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3.11}"
TORCH_INDEX="${TORCH_INDEX:-https://download.pytorch.org/whl/cu124}"
GSPLAT_VERSION="${GSPLAT_VERSION:-1.5.3}"
VENV="$WURZEL/.venv-splat"

echo "== .venv-splat anlegen mit $("$PYTHON" --version)"
"$PYTHON" -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip wheel

echo "== torch (CUDA) von $TORCH_INDEX"
"$VENV/bin/python" -m pip install torch --index-url "$TORCH_INDEX"

echo "== gsplat $GSPLAT_VERSION, open3d, numpy"
# gsplat kompiliert seine CUDA-Kerne beim ersten Rendern (braucht dann das CUDA-Toolkit
# mit nvcc in derselben Fassung wie torch). Vorkompilierte Raeder: siehe
# betrieb/SPLAT_BRUECKE.md, Abschnitt «gsplat ohne Kompilieren».
"$VENV/bin/python" -m pip install "gsplat==$GSPLAT_VERSION" open3d numpy

echo "== Pruefen: Versionen und CUDA"
"$VENV/bin/python" - <<'PY'
import gsplat, numpy, open3d, torch
print("torch", torch.__version__, "cuda", torch.version.cuda,
      "verfuegbar", torch.cuda.is_available())
print("gsplat", gsplat.__version__, "open3d", open3d.__version__, "numpy", numpy.__version__)
if not torch.cuda.is_available():
    raise SystemExit("torch sieht keine CUDA-Karte — gsplat wuerde nicht rendern. "
                     "TORCH_INDEX passend zum Treiber waehlen (nvidia-smi).")
PY

echo "== Probelauf: synthetischer Splat -> Netz (echtes gsplat, kein Ersatzrenderer)"
PROBE="$(mktemp -d)"
trap 'rm -rf "$PROBE"' EXIT
python3 "$WURZEL/tools/make_test_splat.py" "$PROBE/splat.ply" --punkte 20000
"$VENV/bin/python" "$WURZEL/src/aiimaging/runners/splat_zu_netz_runner.py" \
    "$PROBE/splat.ply" "$PROBE/netz.ply" --report "$PROBE/bericht.json" > /dev/null
"$VENV/bin/python" - "$PROBE/bericht.json" <<'PY'
import json, sys
b = json.load(open(sys.argv[1], encoding="utf-8"))
print("status", b["status"], "renderer", b["renderer"], "geraet", b["geraet"])
print("netz", b["netz"]["ecken"], "Ecken,", b["netz"]["dreiecke"], "Dreiecke;",
      "Blickwinkel", b["blickwinkel"]["gesamt"], "; Zeit", b["zeiten_s"]["gesamt_s"], "s")
PY
echo "== fertig. Die Bruecke ist eingerichtet: $VENV"
