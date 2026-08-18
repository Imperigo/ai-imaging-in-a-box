# Lizenzprüfung · was die Binärpakete mitbringen, und was ihre Wheel-Angabe verschweigt

**Stand:** 2026-08-18 · **Auftrag:** die Wissensschuld „Binärabhängigkeiten ungeprüft"
abtragen (`docs/PLAN.md`, Abschnitt Wissensschulden)
**Prüfraster:** Regel 1 aus `CLAUDE.md` — permissiv, kein GPL/AGPL. Und der Satz aus der
Lagebeurteilung, der diesen Auftrag begründet: *Ein fertiges Wheel verbirgt, was
einkompiliert ist. Die Lizenzangabe des PyPI-Pakets sagt nichts über die statisch
eingebundenen Bibliotheken.*

---

## 0 · Was hier gemacht wurde, und was nicht

Die Lizenzprüfung vom selben Tag (`docs/LIZENZPRUEFUNG_2026-08-18.md`) hat gezeigt, dass
eine Sekundärquelle **in die gefährliche Richtung** falsch lag: Krita AI Diffusion war als
MIT geführt und ist GPL-3.0. Dieselbe Fehlerklasse eine Ebene tiefer ist ein Wheel, das
„BSD-3-Clause" deklariert und intern LGPL- oder GPL-Bibliotheken mitlinkt. Genau danach
wurde hier gesucht — und zwar nicht in Lizenzdatenbanken, sondern **im Wheel selbst**.

**Prüfweg.** Drei Wege, in dieser Reihenfolge der Verlässlichkeit:

1. **Am installierten Binary.** Für alles, was in `.venv-ifc` liegt, wurde die Datei auf
   der Platte untersucht: `dist-info/METADATA`, die mitgelieferten Lizenzdateien, die
   Verzeichnisse `*.libs/`, und für `ifcopenshell` ein Symbol-/Stringlauf über die
   155-MB-`.so`.
2. **Am Wheel auf PyPI, ohne es zu installieren.** Für `torch`, `Pillow`, `triton`,
   `opencv-python`, `cryptography` und die NVIDIA-Pakete wurde das Wheel per
   HTTP-Range-Anfrage als ZIP geöffnet und **nur** das Zentralverzeichnis plus die
   Lizenzdateien gelesen. Das ist die härteste erreichbare Quelle: nicht die Angabe über
   das Artefakt, sondern das Artefakt.
3. **Beim Urheber der Fremdkomponente.** Wo eine Komponente auffiel, wurde ihre Lizenz
   beim Herausgeber nachgelesen (GCC für `libgomp`/`libgfortran`/`libquadmath`, CGAL für
   `Nef_3` und `Polygon_mesh_processing`).

**Einschränkungen vorweg**, damit niemand mehr aus diesem Bericht liest als drinsteht:

- **`github.com` und `api.github.com` sind aus dieser Umgebung gesperrt** (HTTP 403 am
  Agent-Proxy); erreichbar ist `raw.githubusercontent.com`. Zusätzlich nicht erreichbar:
  **`www.cgal.org`** (403) und **`gmplib.org`** (Verbindungsabbruch). Wo das eine Aussage
  betrifft, steht es unten als *ungeprüft*.
- **Statisch gelinkte Bibliotheken lassen sich nicht vollständig aufzählen.** Was in
  `libtorch_cpu.so` (438 MB) oder `libtriton.so` (462 MB) einkompiliert ist, ist ohne
  vollständigen Download und Symbolanalyse nicht abschliessend feststellbar. Für `torch`
  ersetzt die mitgelieferte Sammeldatei `third_party/` diese Analyse weitgehend; für
  **Rust-Wheels** (`tokenizers`, `safetensors`, `hf-xet`, `pydantic-core`) gibt es
  überhaupt keine Sammeldatei — dieser Posten bleibt offen (§6).
- **Dies ist keine Rechtsberatung**, sondern eine technische Einordnung.

**Nicht Gegenstand:** Modellgewichte (erledigt in `LIZENZPRUEFUNG_2026-08-18.md`) und
Blender (steht als GPL-Komponente im `NOTICE`, Aufruf als Subprozess).

---

## 1 · Welche Binärpakete überhaupt in Frage kommen

`pyproject.toml` hat mit Absicht **null Laufzeitabhängigkeiten**. Der Kern ist reine
stdlib. Binärcode betritt dieses Projekt nur an vier Stellen:

| Ort | wie | was |
|---|---|---|
| **Produkt-venv, lokaler Import** | `render.py` Z. 404–405, `tiefenschaetzer.py` Z. 627–628, beide **innerhalb** der Ladefunktion | `torch`, `diffusers`, `transformers`, und über `PIL.Image` (Z. 447 bzw. 659) `Pillow` |
| **Produkt-venv, transitiv** | von `diffusers`/`transformers` nachgezogen | `numpy`, `safetensors`, `tokenizers`, `huggingface-hub`, `hf-xet` |
| **Produkt-venv, optional** | `[project.optional-dependencies] mcp` | `mcp` → `pyjwt[crypto]` → `cryptography` (statisch gelinktes OpenSSL) |
| **`.venv-ifc`, jenseits der Prozessgrenze** | `ifc_to_glb_runner.py` Z. 43–44 | `ifcopenshell`, `trimesh`, `numpy`, `shapely`, `lark`, `isodate`, `python-dateutil`, `six` |

**`opencv` liegt in keinem Pfad dieses Projekts.** Der einzige Treffer im Repo ist
`tests/test_bildlesen.py` Z. 998, wo `cv2` auf einer **Verbotsliste** steht — der Test
bewacht, dass der EXR-Leser ohne OpenCV auskommt. Weder `diffusers` (Pflichtabhängigkeiten:
`importlib_metadata`, `filelock`, `httpx`, `huggingface-hub`, `numpy`, `regex`, `requests`,
`safetensors`, `Pillow`) noch `transformers` fordern es. Die Formulierung der
Wissensschuld war an dieser Stelle also zu weit gefasst. Weil die Frage nach FFmpeg im
OpenCV-Wheel trotzdem eine echte ist — und weil OpenCV das naheliegendste Paket ist, das
jemand später hinzufügt —, ist sie in §5 **vorsorglich** beantwortet.

---

## 2 · Das Ergebnis in einem Satz

**Geprüft wurden 39 Pakete.** In ihnen wurden **79 namentlich benannte Fremdkomponenten**
gefunden, die nicht das Paket selbst sind. Die Zählung, damit sie nachrechenbar ist:
36 aus `torch` (34 Einträge unter `third_party/`, dazu `libgomp` und der cpr-GPL-Text),
19 aus `Pillow` (18 mitgelieferte Bibliotheken plus das nachgeladene FriBidi), 9 aus
`ifcopenshell`, 6 aus `triton`, 3 aus `numpy`, je 1 aus `shapely` und `cryptography`,
4 aus dem NVIDIA-EULA (LLVM, Thrust, PCRE, GDB). *(OpenCV mit weiteren rund 45 Komponenten
ist hier nicht mitgezählt — es liegt in keinem Pfad, siehe §5.)*

Davon sind **drei copyleft** — CGAL (**GPL-3.0-or-later**), GEOS (**LGPL-2.1**),
libquadmath (**LGPL-2.1-or-later**) —, **zwei GPL mit Ausnahmeklausel** (libgomp,
libgfortran), **eine Dual-Lizenz, bei der man aktiv wählen muss** (FreeType: FTL oder
GPL-2.0), und **eine reine GPL-3.0-Lizenzdatei ohne zugehörigen Code** (cpr/test in
`torch`). Dazu sind **16 der 39 Pakete NVIDIA-proprietär** — nicht copyleft, aber auch
nicht permissiv, mit Weitergabeschranke und ausdrücklicher Open-Source-Klausel.
**AGPL wurde nirgends gefunden.**

Der praktisch folgenreichste Fund ist kein GPL-Fund, sondern die Erkenntnis, dass
`pip install torch` auf Linux **zwingend** mehr als 1,5 GB proprietärer
NVIDIA-Binärdateien nachzieht (§4.4) — und dass ein Paket, das sich als MIT ausweist
(`triton`), davon rund 90 MB im eigenen Wheel mitliefert, ohne die zugehörige Lizenz auch
nur zu erwähnen (§4.5).

---

## 3 · Die Tabelle

Abrufdatum durchgehend **2026-08-18**. „Deklariert" ist der **wörtliche** Bezeichner aus
`METADATA` bzw. `dist-info`, nicht meine Übersetzung.

### 3a · Produkt-venv — was beim Rendern wirklich importiert wird

| Paket | deklarierte Lizenz | mitgebrachte Fremdlizenzen (Komponente → Lizenz) | Quelle | Urteil (Regel 1) |
|---|---|---|---|---|
| **torch 2.13.0** | `License-Expression: Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT` | **34 Komponenten** in `dist-info/licenses/third_party/`, 98 Lizenzdateien. Permissiv: FP16, FXdiv, VulkanMemoryAllocator, aiter, composable_kernel, cpp-httplib, cudnn_frontend, fmt, ideep, mimalloc, miniz, psimd (MIT); NNPACK, cpuinfo, pthreadpool, python-peachpy (BSD-2); XNNPACK, cutlass, fbgemm, flash-attention, gloo, googletest, kineto, mslk, protobuf, pybind11, tensorpipe (BSD-3); benchmark, flatbuffers, gemmlowp, onnx (Apache-2.0); NVTX, llvm-openmp (Apache-2.0 WITH LLVM-exception); sleef (BSL-1.0). **Nicht deklariert, aber im Wheel:** `torch/lib/libgomp.so.1` → **GPL-3.0-or-later WITH GCC-exception-3.1**. **GPL-Textfund:** `third_party/kineto/…/dynolog/…/cpr/test/LICENSE` → **GPL-3.0** | Wheel `torch-2.13.0-cp311-cp311-manylinux_2_28_x86_64.whl`, Zentralverzeichnis + Lizenzdateien per Range-Abruf; https://pypi.org/pypi/torch/json | ⚠️ **zulässig mit Vorbehalt** — §4.1, §4.2 |
| **diffusers 0.39.0** | `Apache 2.0 License` (Klassifikator) | keine — reines Python, kein Binäranteil | https://pypi.org/pypi/diffusers/json; LICENSE-Datei bereits am 2026-08-18 bestätigt | ✅ zulässig |
| **transformers 5.15.0** | `Apache 2.0 License` (Klassifikator) | keine — reines Python | dito | ✅ zulässig |
| **Pillow 12.3.0** | `License-Expression: MIT-CMU` | **18 Bibliotheken** in `pillow.libs/`: brotli (MIT), bzip2 (BSD-artig), dav1d (BSD-2), **FreeType (FTL *oder* GPL-2.0-or-later — Wahlrecht)**, HarfBuzz (MIT), lcms2 (MIT), libavif (BSD-2), libjpeg (IJG), **liblzma (Public Domain**, LGPL-/GPL-Teile des XZ-Pakets „end up" laut Text **nicht** im Binary), libpng (zlib/libpng), libtiff (BSD-artig), libwebp (BSD-3), libyuv (BSD-3), OpenJPEG (BSD-2), Raqm (MIT), XDMCP/XCB (MIT), zlib, zstd (BSD-3). **Zur Laufzeit nachgeladen, nicht mitgeliefert:** FriBidi (**LGPL-2.1-or-later**) über `dlopen` | Wheel `pillow-12.3.0-cp311-…x86_64.whl`, Datei `dist-info/licenses/LICENSE` (70 KB) und `readelf -d` auf `_imagingft…so` | ✅ zulässig — §4.3 |
| **numpy 2.4.6** (installiert) | `License-Expression: BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0` | **3 Bibliotheken** in `numpy.libs/`, **keine davon in der License-Expression genannt**: `libscipy_openblas64_` → OpenBLAS 0.3.31 (BSD-3), `libgfortran.so.5` → **GPL-3.0-or-later WITH GCC-exception-3.1**, `libquadmath.so.0` → **LGPL-2.1-or-later** | `.venv-ifc/lib/python3.11/site-packages/numpy.libs/`, `numpy-2.4.6.dist-info/METADATA`; Lizenzen aus GCC-Quellköpfen (unten) | ⚠️ **zulässig mit Vorbehalt** — §4.2 |
| **safetensors 0.8.0** | `License :: OSI Approved :: Apache Software License` | keine ausgewiesen; `_safetensors_rust.abi3.so` (1,2 MB) enthält statisch gelinkte Rust-Kisten, die **nirgends aufgezählt** sind | Wheel-Inhalt (2 Dateien: `.so` + `licenses/LICENSE`, Apache-2.0-Volltext); https://raw.githubusercontent.com/huggingface/safetensors/main/LICENSE | ⚠️ **Eigenlizenz bestätigt, Fremdanteil ungeprüft** — §5 |
| **tokenizers 0.23.1** | nur Klassifikator `Apache Software License` — **keine Lizenzdatei im Wheel** | keine ausgewiesen; `tokenizers.abi3.so` = 10,3 MB Rust-Binary | Wheel-Inhalt (32 Einträge, kein `LICENSE`); Volltext nur am Quellrepo: https://raw.githubusercontent.com/huggingface/tokenizers/main/LICENSE (Apache-2.0) | ⚠️ dito, zusätzlich **Lizenzdatei fehlt im Artefakt** |
| **huggingface-hub 1.28.0** | `Apache-2.0` | keine — reines Python | https://pypi.org/pypi/huggingface-hub/json | ✅ zulässig |
| **hf-xet 1.6.0** | `licenses/LICENSE` = Apache-2.0-Volltext | keine ausgewiesen; `hf_xet.abi3.so` = 12,2 MB Rust-Binary | Wheel-Inhalt | ⚠️ wie safetensors |
| **cryptography 50.0.0** *(nur über `[mcp]`)* | `License-Expression: Apache-2.0 OR BSD-3-Clause` | **nicht deklariert:** `_rust.abi3.so` (14,3 MB) linkt **OpenSSL 4.0.1** statisch ein (Apache-2.0), Stringbefund auch `BORINGSSL`. Im Wheel liegen **nur** die eigenen `LICENSE.APACHE` und `LICENSE.BSD` | Wheel `cryptography-50.0.0-cp311-abi3-…x86_64.whl`, `strings` auf `_rust.abi3.so` | ✅ zulässig (OpenSSL 3+/4 ist Apache-2.0), **aber undeklariert** |
| **pydantic-core 2.48.0**, **jiter 0.16.0** *(nur über `[mcp]`)* | `License-Expression: MIT` | nicht aufgezählt (Rust) | https://pypi.org/pypi/pydantic-core/json | ✅ zulässig, Fremdanteil ungeprüft |

### 3b · Was `pip install torch` auf Linux **zwingend** mitinstalliert

Alle folgenden Einträge sind in `torch` 2.13.0 als `Requires-Dist` mit der Bedingung
`platform_system == "Linux"` geführt — **kein Extra, keine Option**.

| Paket | deklarierte Lizenz | Inhalt / Fremdlizenzen | Quelle | Urteil (Regel 1) |
|---|---|---|---|---|
| **cuda-toolkit 13.3.1** | keine Angabe (`license_expression: None`) | Metapaket; die von `torch` verlangten Extras `cublas, cudart, cufft, cufile, cupti, curand, cusolver, cusparse, nvjitlink, nvrtc, nvtx` ziehen elf einzelne `nvidia-*`-Wheels nach | https://pypi.org/pypi/cuda-toolkit/json | ⛔ **nicht permissiv** — §4.4 |
| **nvidia-cuda-runtime 13.3.29** *(stellvertretend geprüft)* | `License-Expression: LicenseRef-NVIDIA-Proprietary` | `licenses/License.txt` = 59 200 Zeichen **NVIDIA End User License Agreement** (SDK-Vertrag vom 26.07.2018 + CUDA-Toolkit-Supplement). Darin als Fremdkomponenten genannt: LLVM (NCSA), Thrust (Apache-2.0), Boost (BSL-1.0), PCRE (BSD) — **und GDB unter GPL v3** sowie ein LGPL-Quellcode-Angebot (`oss-requests@nvidia.com`), beides für Teile des Toolkits, die in **diesem** Wheel nicht enthalten sind (der Wheel-Inhalt ist `libcudart` plus Header) | Wheel `nvidia_cuda_runtime-13.3.29-…x86_64.whl`, Datei `dist-info/licenses/License.txt` + `METADATA`, vollständig heruntergeladen | ⛔ **nicht permissiv** — §4.4 |
| **nvidia-cublas 13.6.1.10** | `License-Expression: LicenseRef-NVIDIA-Proprietary` | 410 MB Binärbibliothek | https://pypi.org/pypi/nvidia-cublas/json | ⛔ nicht permissiv |
| **nvidia-cuda-cupti / -nvrtc / -runtime / cufft / cufile / curand / cusolver / cusparse / nvjitlink / nvtx** | keine `license_expression` in den PyPI-Metadaten; dieselbe `License.txt` im Wheel | dito | https://pypi.org/pypi/&lt;name&gt;/json | ⛔ nicht permissiv |
| **nvidia-cudnn-cu13 9.24.0.43** | keine Angabe | 553 MB (x86_64) | https://pypi.org/pypi/nvidia-cudnn-cu13/json | ⛔ nicht permissiv |
| **nvidia-cusparselt-cu13 0.9.1** | `License: NVIDIA Proprietary Software` | 171 MB | dito | ⛔ nicht permissiv |
| **nvidia-nccl-cu13 2.31.2** | keine Angabe (NCCL selbst ist BSD-3, **hier nicht am Artefakt belegt**) | 252 MB | dito | ⚠️ **ungeprüft** |
| **nvidia-nvshmem-cu13 3.7.2** | keine Angabe | 135 MB | dito | ⚠️ **ungeprüft** |
| **cuda-bindings 13.3.1** | `License-Expression: LicenseRef-NVIDIA-SOFTWARE-LICENSE` | Python-Bindings | https://pypi.org/pypi/cuda-bindings/json | ⛔ nicht permissiv |
| **triton 3.7.1** | `License :: OSI Approved :: MIT License`; `licenses/LICENSE` = MIT-Text (Tillet/OpenAI) | **Im Wheel, ohne jede zugehörige Lizenzdatei:** `backends/nvidia/bin/ptxas` (31,9 MB), `ptxas-blackwell` (41,4 MB), `cuobjdump` (0,7 MB, String „Copyright (c) 2005-%s NVIDIA Corporation"), `nvdisasm` (5,0 MB), `lib/cupti/libcupti.so`, `libnvperf_host.so`, `libnvperf_target.so`, `libcheckpoint.so`, `libpcsamplingutil.so` — zusammen ~90 MB **NVIDIA-proprietär**. Dazu `_C/libtriton.so` (462 MB) mit statisch gelinktem LLVM/MLIR (Apache-2.0 WITH LLVM-exception), ebenfalls undeklariert | Wheel `triton-3.7.1-cp311-…x86_64.whl`, Zentralverzeichnis + `dist-info/licenses/LICENSE` + `strings` auf entpacktem `cuobjdump` | ⛔ **Deklaration unvollständig** — §4.5 |

### 3c · `.venv-ifc` — jenseits der Prozessgrenze

| Paket | deklarierte Lizenz | mitgebrachte Fremdlizenzen | Quelle | Urteil (Regel 1) |
|---|---|---|---|---|
| **ifcopenshell 0.8.5** | Klassifikator `GNU Lesser General Public License v3 or later (LGPLv3+)` | Statisch in `_ifcopenshell_wrapper…so` (155 MB), per Stringlauf am installierten Binary: **CGAL** (9 824 Treffer; darunter `Nef_polyhedron_3` 249, `Polygon_mesh_processing` 47, `convex_decomposition` 8) → **GPL-3.0-or-later**; **Open CASCADE** (`TopoDS` 317, `BRepAlgoAPI` 9, `opencascade` 154) → LGPL-2.1 mit Zusatzausnahme; **GMP** (`__gmp*` 332) → LGPL-3/GPL-2 dual *(nicht am Original geprüft, §5)*; **MPFR** (6) → LGPL-3+ *(dito)*; **Boost** (38 801) → BSL-1.0; **Eigen** (88) → MPL-2.0; **nlohmann/json** (109) → MIT; **HDF5** (`H5F` 485) → BSD-3-artig; **libxml2** (5) → MIT | Installierte Datei `.venv-ifc/lib/python3.11/site-packages/ifcopenshell/…so`; CGAL-Einordnung am Original: https://raw.githubusercontent.com/CGAL/cgal/master/Nef_3/package_info/Nef_3/license.txt (= „GPL (v3 or later)") u. a. | ⛔ **GPL-Fund** — §4.6, **bestätigt**; zulässig **nur** hinter der Prozessgrenze |
| **shapely 2.1.2** | `License: BSD 3-Clause` | `shapely.libs/libgeos-…so.3.13.1` + `libgeos_c-…so.1.19.2` → **GEOS unter LGPLv2.1**. Das Paket sagt es selbst, in einer zweiten Lizenzdatei: `licenses/LICENSE_GEOS`, Kopfzeile „Name: Geometry Engine Open Source (GEOS) … License: LGPLv2.1" | `.venv-ifc/…/shapely-2.1.2.dist-info/licenses/LICENSE_GEOS` und `shapely.libs/` | ⚠️ **LGPL-Fund** — §4.7; zulässig, weil hinter der Prozessgrenze |
| **numpy 2.4.6** | siehe 3a | siehe 3a (libgfortran GPL+Ausnahme, libquadmath LGPL-2.1+, OpenBLAS BSD-3) | siehe 3a | ⚠️ siehe §4.2 |
| **trimesh 5.0.0** | `License: The MIT License (MIT)` | keine mitgelieferten Binaries | `.venv-ifc/…/trimesh-5.0.0.dist-info/licenses/LICENSE.md` | ✅ zulässig |
| **lark 1.3.1** | `License: MIT` | keine | `.venv-ifc/…/lark-1.3.1.dist-info/licenses/LICENSE` | ✅ zulässig |
| **isodate 0.7.2** | Klassifikator `BSD License` | keine | `.venv-ifc/…/isodate-0.7.2.dist-info/LICENSE` | ✅ zulässig |
| **python-dateutil 2.9.0.post0** | `License: Dual License`, Klassifikatoren BSD **und** Apache — Datei nennt „Apache License, Version 2.0" | keine | `.venv-ifc/…/python_dateutil-…dist-info/LICENSE` | ✅ zulässig |
| **six 1.17.0** | `License: MIT` | keine | `.venv-ifc/…/six-1.17.0.dist-info/LICENSE` | ✅ zulässig |

---

## 4 · Die Funde, einzeln

### 4.1 torch bringt eine GPL-3.0-Lizenzdatei mit — ausdrücklich als GPL-Fund gemeldet

**Regel 1 verlangt, dass GPL-Funde als solche benannt werden, also hier:** Im
`torch`-Wheel liegt unter

```
torch-2.13.0.dist-info/licenses/third_party/kineto/libkineto/third_party/
    dynolog/third_party/cpr/test/LICENSE
```

der **vollständige Text der GNU General Public License Version 3**, eingeleitet mit dem
Satz „This license applies to everything inside this directory and all subdirectories."
Es ist die einzige der 98 Lizenzdateien im Wheel, die Copyleft trägt.

Was sie abdeckt: das **Testverzeichnis** von *cpr* (C++ Requests), das über *dynolog* unter
*kineto* (PyTorchs Profiler) eingebunden ist. Was dagegen im Wheel **nicht** liegt: irgendein
cpr- oder dynolog-Quell- oder Objektcode. Die Suche über alle 12 911 Wheel-Einträge nach
`cpr` und `dynolog` liefert **ausschliesslich Lizenzdateien**; von `kineto` sind nur 20
Header unter `torch/include/kineto/` enthalten. Der Befund ist damit: **die Lizenz ist
mitgereist, der Code nicht.** Ursache ist mit hoher Wahrscheinlichkeit ein
Sammel-Glob im Verpackungsschritt, der `third_party/**/LICENSE*` einpackt.

Warum das trotzdem hier steht und nicht weggelassen wird: Wer dieses Wheel später auf GPL
prüft — mit einem Werkzeug, das nach Lizenztexten sucht, und das ist die übliche Methode —
**bekommt genau diesen Treffer** und muss ihn einordnen können. Ein unerklärter GPL-Treffer
in einer Auslieferung ist teurer als ein erklärter.

Ein zweiter Punkt zur Sorgfalt: Der erste automatische Durchlauf meldete an derselben
Stelle zusätzlich *AGPL*. Das war ein **Fehlalarm meines eigenen Prüfmusters** — der
GPLv3-Text nennt in §13 die „GNU Affero General Public License". **Es ist kein AGPL-Fund.**
In keinem der geprüften Pakete wurde AGPL gefunden.

### 4.2 `libgomp`, `libgfortran`, `libquadmath` — GNU-Bibliotheken in Wheels, die sie nicht deklarieren

Drei Bibliotheken der GCC-Laufzeit reisen als fertige `.so` in Wheels mit, deren
Lizenzangabe sie **nicht erwähnt**:

| Datei | wo | Lizenz laut Quellkopf beim Urheber |
|---|---|---|
| `torch/lib/libgomp.so.1` (254 009 Bytes) | `torch`-Wheel | GPL-3.0-or-later **WITH GCC-exception-3.1** |
| `numpy.libs/libgfortran-…so.5.0.0` (2,8 MB) | `numpy`-Wheel | GPL-3.0-or-later **WITH GCC-exception-3.1** |
| `numpy.libs/libquadmath-…so.0.0.0` (251 KB) | `numpy`-Wheel | **LGPL-2.1-or-later** („GNU Library General Public License … version 2, or (at your option) any later version") |

Belegt ist das doppelt: an den Binärdateien selbst (`strings` auf `libgomp.so.1` zeigt
GCC-Quellpfade `../../../libgomp/oacc-init.c`; `libgfortran` zeigt
`../../../libgfortran/generated/matmul_*.c`) und an den Quellköpfen beim Urheber
— https://raw.githubusercontent.com/gcc-mirror/gcc/master/libgomp/libgomp.h,
`libgfortran/libgfortran.h`, `libquadmath/quadmath.h`.

Und das Wesentliche: **Beide Wheels schweigen dazu.** `numpy` deklariert
`BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0` und liefert 17 Lizenzdateien mit — für
Quellcode im eigenen Baum (pocketfft, highway, libdivide, dragon4, …). Für die drei
`.so`-Dateien in `numpy.libs/`, die pip tatsächlich installiert, ist **keine einzige**
dabei. Bei `torch` ist es dasselbe: 34 Komponenten sauber dokumentiert, `libgomp` nicht.
Das ist exakt das Muster, das dieser Auftrag suchen sollte — nur diesmal nicht bösartig,
sondern schlicht ausgelassen.

**Wie schwer wiegt es?** Die **GCC Runtime Library Exception 3.1** ist genau für diesen
Fall geschrieben. Ihr Kernsatz, im Original abgerufen
(https://raw.githubusercontent.com/gcc-mirror/gcc/master/COPYING.RUNTIME):

> You have permission to propagate a work of Target Code formed by combining the Runtime
> Library with Independent Modules, even if such propagation would otherwise violate the
> terms of GPLv3, provided that all Target Code was generated by Eligible Compilation
> Processes. You may then convey such a combination under terms of your choice […]

„Eligible" heisst dabei: übersetzt mit GCC oder mit GPL-kompatibler Software, oder ganz
ohne GCC-basierte Werkzeuge. Manylinux-Wheels werden mit GCC gebaut. Die Bedingung ist
also erfüllt, und `libgomp`/`libgfortran` machen das Produkt **nicht** GPL.

`libquadmath` ist der interessantere der drei: Es steht **nicht** unter GPL+Ausnahme,
sondern unter der **LGPL**. Damit greift die LGPL-Präzisierung aus `CLAUDE.md` — und die
verlangt eine Prozessgrenze. Praktisch ist die Auflage hier ohne Zutun erfüllt:
`libquadmath` wird von `libgfortran` als **dynamische** Bibliothek geladen, unverändert
mitgeliefert und ist gegen eine andere Fassung austauschbar. Die dritte Auflage —
**„deklariert"** — ist die einzige, die dieses Projekt noch schuldet: Im `NOTICE` steht
davon nichts (§7).

### 4.3 Pillow ist sauber — und zeigt dabei die Prozessgrenze in Miniaturform

Pillow deklariert `MIT-CMU` und liefert 18 native Bibliotheken mit. Die 70-KB-Lizenzdatei
im Wheel benennt sie einzeln (BROTLI, BZIP2, DAV1D, FREETYPE2, HARFBUZZ, LCMS2, LIBAVIF,
LIBJPEG, LIBLZMA, LIBPNG, LIBTIFF, LIBWEBP, LIBYUV, OPENJPEG, RAQM, XDMCP, ZLIB, ZSTD).
Das ist eine vorbildliche Deklaration. Zwei Punkte gehören trotzdem aufgeschrieben:

**FreeType ist dual lizenziert, und man muss wählen.** Der mitgelieferte Text sagt es
wörtlich: „we distribute it under two mutually exclusive open-source licenses. This means
that *you* must choose *one* of the two" — die FreeType License (BSD-artig, **mit
Werbeklausel**: das Projekt muss in der Produktdokumentation genannt werden) oder die
**GPL-2.0-or-later**. Für dieses Projekt ist die Wahl trivial (FTL), aber sie ist eine
Wahl, und die Werbeklausel ist eine Auflage, die ins `NOTICE` gehört. Wer nicht wählt, hat
faktisch nichts gewählt.

**FriBidi wird zur Laufzeit geladen, nicht mitgeliefert.** In `_imagingft…so` stehen
FriBidi-Symbolnamen, und das liest sich zunächst wie ein LGPL-Fund. Der Blick in die
ELF-Struktur widerlegt es: `readelf -d` zeigt als `DT_NEEDED` nur
`libfreetype`, `libharfbuzz`, `libpthread`, `libc` — **kein FriBidi**; `nm -D` findet kein
einziges FriBidi-Symbol; stattdessen enthält die Datei `dlopen` und die Namensliste
`libfribidi.so.0`, `libfribidi.so`, `libfribidi.dylib`. Raqm lädt FriBidi (LGPL-2.1+)
**optional zur Laufzeit** nach, wenn es auf dem System liegt, und nur für die
Rechts-nach-links-Textformung. Im Wheel ist es nicht.

Das ist bemerkenswert, weil es dieselbe Lösung ist, die dieses Projekt zweimal selbst
gewählt hat — die Grenze zwischen „einverleibt" und „zur Laufzeit angesprochen". Pillow
zieht sie über `dlopen`, wir über den Subprozess. Für unseren Pfad ist die Konsequenz
angenehm: **Solange kein FriBidi auf dem System liegt, kommt keine LGPL-Bibliothek in den
Prozess** — und Rechts-nach-links-Textformung braucht eine Bildkette nicht.

### 4.4 Der eigentliche Fund: `torch` zieht auf Linux zwingend proprietäre NVIDIA-Binärdateien nach

Das ist kein GPL-Problem und deshalb umso leichter zu übersehen. `torch` 2.13.0 führt in
seinen `Requires-Dist` **ohne Extra-Bedingung**, nur mit `platform_system == "Linux"`:

```
cuda-toolkit[cublas,cudart,cufft,cufile,cupti,curand,cusolver,cusparse,nvjitlink,nvrtc,nvtx]==13.0.3
cuda-bindings>=13.0.3,<14
nvidia-cudnn-cu13==9.20.0.48
nvidia-cusparselt-cu13==0.8.1
nvidia-nccl-cu13==2.29.7
nvidia-nvshmem-cu13==3.4.5
triton==3.7.1
```

Ein `pip install torch` auf der HomeStation installiert damit deutlich über ein Gigabyte
Binärcode, dessen Lizenz **weder permissiv noch copyleft** ist. Die Wheels tragen
`License-Expression: LicenseRef-NVIDIA-Proprietary` bzw.
`LicenseRef-NVIDIA-SOFTWARE-LICENSE`, `nvidia-cusparselt-cu13` schlicht
`License: NVIDIA Proprietary Software`.

Der Vertragstext liegt jedem Wheel bei (`dist-info/licenses/License.txt`, 59 200 Zeichen,
hier aus `nvidia_cuda_runtime-13.3.29` gelesen). Vier Stellen sind für ein **öffentliches
Apache-2.0-Repo** relevant:

1. **Weitergabe nur eingebettet, nie für sich.** §1.2(2): „you may not distribute or
   sublicense the SDK as a stand-alone product." §1.1.2 verlangt zusätzlich, dass die
   eigene Anwendung „material additional functionality" über das SDK hinaus hat und dass
   die verteilbaren Teile „shall only be accessed by your application".
2. **Kein Reverse Engineering, keine Entfernung von Hinweisen** (§1.2(1)).
3. **Die Open-Source-Klausel**, §1.2(5), wörtlich:

   > You may not use the SDK in any manner that would cause it to become subject to an
   > open source software license. As examples, licenses that require as a condition of
   > use, modification, and/or distribution that the SDK be: a. Disclosed or distributed
   > in source code form; b. Licensed for the purpose of making derivative works; or
   > c. Redistributable at no charge.

4. **Nur für NVIDIA-Hardware** (§2.1) und **nicht für lebenskritische Anwendungen** (§1.2(6)).

**Wie das dieses Projekt trifft.** Apache-2.0 verlangt weder Quelloffenlegung noch
kostenlose Weitergabe des kombinierten Werks; Klausel 5 ist durch die eigene Lizenz also
nicht ausgelöst. Sie ist aber ein sehr konkretes Verbot, **CUDA und eine GPL-Komponente in
ein Programm zu legen** — und dieses Projekt hat zwei GPL-Komponenten im Haus (Blender,
CGAL in IfcOpenShell). Die bestehende Architektur beantwortet das bereits: Blender läuft
als eigenes Binary, IfcOpenShell in `.venv-ifc`, `torch` nur im Produkt-venv. **Die
Prozessgrenze, die aus Regel 1 und Regel 2 gezogen wurde, hält hier ein drittes Mal — nur
diesmal gegen eine proprietäre statt gegen eine copyleft Auflage.** Das ist ein
nachträgliches Argument für eine Entscheidung, die aus ganz anderen Gründen getroffen
wurde, und es gehört festgehalten.

Zwei Nebenbefunde:

- **Eine Namensfalle.** Auf PyPI existieren `nvidia-cublas-cu13`, `nvidia-cufft-cu13`,
  `nvidia-curand-cu13`, `nvidia-cusolver-cu13`, `nvidia-cusparse-cu13`,
  `nvidia-cuda-runtime-cu13`, `nvidia-cuda-nvrtc-cu13`, `nvidia-nvjitlink-cu13` — alle in
  Version **0.0.1**, alle mit `License-Expression: Apache-2.0`, alle als **leeres
  `.tar.gz` von 0,0 MB**. Das sind Platzhalter. Die echten Bibliotheken heissen
  `nvidia-cublas` (410 MB, `LicenseRef-NVIDIA-Proprietary`) usw. **Wer eine
  Lizenzaufstellung aus Paketnamen erzeugt, liest hier „Apache-2.0" für cuBLAS.** Das ist
  derselbe Fehler wie bei Krita AI Diffusion, nur ohne Absicht — und er zeigt in dieselbe
  Richtung: permissiv gemeldet, wo es nicht permissiv ist.
- **Zwei NVIDIA-Pakete bleiben ungeprüft:** `nvidia-nccl-cu13` (252 MB) und
  `nvidia-nvshmem-cu13` (135 MB) tragen in den PyPI-Metadaten **überhaupt keine**
  Lizenzangabe. NCCL ist quelloffen unter BSD-3, aber **das habe ich am Artefakt nicht
  belegt** und trage es deshalb nicht als geprüft ein.

### 4.5 `triton` deklariert MIT und liefert 90 MB NVIDIA-Binärdateien mit

Der sauberste Einzelfall des gesuchten Musters, und er sitzt im Pflichtpfad von `torch`.

`triton` 3.7.1 trägt den Klassifikator `License :: OSI Approved :: MIT License`, und die
einzige Lizenzdatei im Wheel — `dist-info/licenses/LICENSE`, 1,2 KB — ist der MIT-Text von
Philippe Tillet und OpenAI. Im selben Wheel liegen:

```
 31.91 MB  triton/backends/nvidia/bin/ptxas
 41.37 MB  triton/backends/nvidia/bin/ptxas-blackwell
  5.01 MB  triton/backends/nvidia/bin/nvdisasm
  0.74 MB  triton/backends/nvidia/bin/cuobjdump
 25.83 MB  triton/backends/nvidia/lib/cupti/libnvperf_host.so
  7.60 MB  triton/backends/nvidia/lib/cupti/libcupti.so
  5.28 MB  triton/backends/nvidia/lib/cupti/libnvperf_target.so
  1.64 MB  triton/backends/nvidia/lib/cupti/libcheckpoint.so
  0.97 MB  triton/backends/nvidia/lib/cupti/libpcsamplingutil.so
461.59 MB  triton/_C/libtriton.so
```

`cuobjdump` wurde entpackt und geprüft: `strings` liefert
`Copyright (c) 2005-%s NVIDIA Corporation`. Das sind NVIDIA-Werkzeuge unter dem EULA aus
§4.4 — **und im gesamten Wheel gibt es dafür keine einzige Lizenzdatei.** Dasselbe gilt für
LLVM/MLIR, das in `libtriton.so` (462 MB) statisch eingebunden ist.

Für Regel 1 ändert das nichts an der Einordnung: Es ist kein Copyleft, `triton` bleibt
benutzbar. Für die **Aussagekraft von Wheel-Lizenzangaben** ändert es alles. Ein Werkzeug,
das Lizenzen aus `dist-info` einsammelt, meldet hier „MIT" für ein Paket, dessen
Auslieferung rund 90 MB proprietäre NVIDIA-Werkzeuge enthält.

### 4.6 CGAL in IfcOpenShell ist GPL-3.0 — am Original bestätigt, nicht nur am Binary

**Ausdrücklich als GPL-Fund gemeldet.** Der Befund vom 2026-08-14 (Lagebeurteilung,
Kapitel 2) stützte sich auf Symbolzählungen im Wheel-Binary. Er wurde hier zweifach
nachgeprüft:

**Am installierten Binary**, `.venv-ifc/…/ifcopenshell/_ifcopenshell_wrapper…so`
(154 982 176 Bytes). Die Zahlen der Lagebeurteilung bestätigen sich exakt:
`Nef_polyhedron_3` **249**, `Polygon_mesh_processing` **47**, `convex_decomposition` **8**.
Neu hinzu kommen `CGAL` insgesamt **9 824** Treffer, Open CASCADE (`TopoDS` 317,
`BRepAlgoAPI` 9), **Boost 38 801**, **`__gmp*` 332**, **Eigen 88**, **nlohmann 109**,
**HDF5 (`H5F`) 485**, libxml2 5. Die `DT_NEEDED`-Liste der Datei nennt nur
`libstdc++`, `libm`, `libgcc_s`, `libc`, `ld-linux` — **alles andere ist statisch drin**.

**Bei CGAL selbst**, über die paketweisen Lizenzdateien im Vorgabezweig:

| CGAL-Paket | Lizenzdatei | Inhalt |
|---|---|---|
| `Nef_3` | `Nef_3/package_info/Nef_3/license.txt` | `GPL (v3 or later)` |
| `Polygon_mesh_processing` | `…/Polygon_mesh_processing/license.txt` | `GPL (v3 or later)` |
| `Convex_decomposition_3` | `…/Convex_decomposition_3/license.txt` | `GPL (v3 or later)` |
| `Kernel_23` (Grundschicht) | `…/Kernel_23/license.txt` | `LGPL (v3 or later)` |

(alle über `https://raw.githubusercontent.com/CGAL/cgal/master/…`, abgerufen 2026-08-18)

Damit ist die Aussage „CGAL ist dual lizenziert, die Grundschicht LGPL, die höheren Pakete
GPL-3.0" **beim Urheber belegt** und nicht mehr nur plausibel. `www.cgal.org/license.html`
war über den Proxy nicht erreichbar (HTTP 403); die paketweisen Dateien sind die bessere
Quelle, weil sie pro Komponente sprechen.

Folge: unverändert. `import ifcopenshell` im Produkt-venv wäre ein GPL-Fund; der Aufruf als
Subprozess in `.venv-ifc` ist es nicht. Die Architektur bleibt richtig.

### 4.7 shapely deklariert BSD-3 und bringt GEOS unter LGPL-2.1 mit

Neuer Fund, in `.venv-ifc`, über `ifcopenshell` hereingezogen (`Requires-Dist: shapely`).

`shapely-2.1.2.dist-info/METADATA` sagt `License: BSD 3-Clause` und
`Classifier: License :: OSI Approved :: BSD License`. Wer nur diese Zeile liest, hält
shapely für permissiv. In `shapely.libs/` liegen aber

```
5 315 353 Bytes  libgeos-3ef06f11.so.3.13.1
  514 225 Bytes  libgeos_c-abcdd5fa.so.1.19.2
```

und shapely sagt selbst, was das ist — in einer **zweiten** Lizenzdatei, die die
`METADATA` als `License-File: LICENSE_GEOS` mitführt:

> This binary distribution of pygeos also bundles the following software:
> Name: Geometry Engine Open Source (GEOS)
> Files: libgeos-\*.so.\*, libgeos_c-\*.so.\*, …
> License: **LGPLv2.1**

Das ist die ehrliche Variante des Musters: Die Kurzangabe ist unvollständig, die
Langangabe stimmt. Wer `License:` liest, irrt; wer `License-File:` liest, nicht.

**Einordnung unter Regel 1.** LGPL, also die Präzisierung vom 2026-08-14. Alle drei
Auflagen sind erfüllt, ohne dass jemand dafür etwas tun musste:
(1) **Prozessgrenze** — shapely liegt ausschliesslich in `.venv-ifc` und wird nur als
Abhängigkeit von `ifcopenshell` geladen, das seinerseits als Subprozess läuft; im
Produkt-venv gibt es kein shapely. (2) **Unverändert** — das Wheel wird so installiert, wie
es kommt. (3) **Austauschbar und deklariert** — austauschbar ja, **deklariert nein**: GEOS
steht nicht im `NOTICE` (§7).

Das ist der einzige Fund dieser Prüfung, der eine **Bringschuld** auslöst statt nur eine
Erkenntnis.

---

## 5 · Vorsorglich beantwortet: was wäre, wenn OpenCV dazukäme

OpenCV liegt in **keinem** Pfad dieses Projekts (§1). Weil die Wissensschuld es nennt und
weil es das naheliegendste Paket ist, das jemand für Bildvorverarbeitung nachträgt, ist die
FFmpeg-Frage hier trotzdem beantwortet — am Artefakt, nicht aus dem Gedächtnis.

Geprüft wurde `opencv-python 5.0.0.93` und `opencv-python-headless 5.0.0.93`
(cp37-abi3-manylinux2014_x86_64), jeweils Zentralverzeichnis plus die mitgelieferte
`LICENSE-3RD-PARTY.txt` (179 609 Zeichen, rund 45 Komponenten).

**Die FFmpeg-Frage hat eine klare Antwort:**

> FFmpeg is redistributed within all opencv-python packages. […] This license applies to
> the above library binaries in the directory cv2/.
> **GNU LESSER GENERAL PUBLIC LICENSE, Version 2.1, February 1999**

Also **LGPL-2.1, nicht GPL.** Im Wheel liegen `libavcodec.so.62`, `libavformat.so.62`,
`libavutil.so.60`, `libswscale.so.9`, `libswresample.so.6`, dazu `libvpx` (BSD-3) und
`libaom` (BSD-2) als Codecs — keine GPL-only-Bibliothek wie x264 oder x265. Das ist die
LGPL-Übersetzung von FFmpeg, ohne `--enable-gpl`.

**Der Unterschied headless / nicht-headless ist hingegen erheblich:**

> Qt 5 is redistributed within non-headless opencv-python Linux and macOS packages. […]
> **GNU LESSER GENERAL PUBLIC LICENSE, Version 3, 29 June 2007**

Bestätigt am Wheel-Inhalt: `opencv-python` enthält `libQt5Core`, `libQt5Gui`,
`libQt5Widgets`, `libQt5Test`, `libQt5XcbQpa` und ein Qt-Plugin — **`opencv-python-headless`
enthält davon nichts.** Für einen Kern ohne Oberfläche (Regel 4) ist headless ohnehin die
richtige Wahl; sie erspart nebenbei eine LGPL-3-Bibliothek.

Weder in `opencv-python` noch in `opencv-python-headless` findet sich ein GPL- oder
AGPL-Text: die Suche nach „GNU GENERAL PUBLIC LICENSE" ohne „LESSER" liefert **null**
Treffer, „AFFERO" ebenfalls null.

**Und der Punkt, der diesen ganzen Bericht zusammenfasst:** Selbst diese sehr sorgfältige,
179 KB lange Deklaration ist **unvollständig**. Im Wheel liegen
`libgfortran-…so.3.0.0` (1,3 MB), `libquadmath-…so.0.0.0` (251 KB),
`libopenblasp-r0-…so` (38,2 MB), `libxkbcommon`, `libdrm`. Die Suche nach „gfortran",
„quadmath", „openblas", „xkbcommon" oder „libdrm" in `LICENSE-3RD-PARTY.txt` liefert
**null Treffer**. Wieder dieselbe GCC-Laufzeit wie in §4.2, wieder undeklariert.

**Zu `opencv-contrib-python` und den Patentmodulen (SIFT/SURF, `xfeatures2d`) wurde nichts
geprüft** — das Paket ist nicht im Pfad, und eine Aussage ohne Prüfung wäre genau der
Fehler, den dieser Bericht abstellen soll.

---

## 6 · Was nicht geprüft werden konnte

Ausdrücklich offen, damit niemand diese Punkte für erledigt hält:

- **Der Inhalt von `libtorch_cpu.so` (438 MB), `libtorch_cuda.so` (470 MB) und
  `libtriton.so` (462 MB).** Was dort statisch einkompiliert ist, wurde **nicht**
  verifiziert. Für `torch` deckt die mitgelieferte `third_party/`-Sammlung den Anspruch
  weitgehend ab; für `triton` gibt es überhaupt keine, und die LLVM-Einbindung ist nur
  aus dem Bauprozess bekannt, nicht am Binary belegt.
- **Die Rust-Wheels.** `tokenizers` (10,3 MB), `safetensors` (1,2 MB), `hf-xet` (12,2 MB),
  `pydantic-core`, `jiter` linken ihre Kisten (crates) statisch ein und liefern **keine
  Aufstellung** mit. Bei `tokenizers` fehlt sogar die eigene Lizenzdatei im Wheel. Das
  Rust-Ökosystem ist ganz überwiegend MIT/Apache-2.0 — **belegt ist das hier nicht.**
  Wer diese Schuld schliessen will, braucht `cargo-license` gegen die jeweilige
  `Cargo.lock`, nicht das Wheel.
- **`nvidia-nccl-cu13` und `nvidia-nvshmem-cu13`** — keine Lizenzangabe in den
  PyPI-Metadaten, Wheel-Inhalt nicht geprüft (252 bzw. 135 MB).
- **GMP und MPFR in IfcOpenShell** — im Binary nachgewiesen (`__gmp*` 332 Treffer,
  `mpfr_*` 6), aber die Lizenz **nicht am Original geprüft**: `gmplib.org` war über den
  Proxy nicht erreichbar (Verbindungsabbruch). Beide gelten gemeinhin als LGPL-3-or-later
  bzw. dual GPL-2 — das ist hier **Hörensagen und wird als solches markiert.** Es liegt
  jenseits der Prozessgrenze und ist deshalb nicht dringend, aber es ist offen.
- **`www.cgal.org/license.html`** (HTTP 403) — die Gesamtübersicht des Projekts. Ersetzt
  durch die paketweisen `license.txt`-Dateien, die die bessere Quelle sind (§4.6).
- **Open CASCADE** — im Binary nachgewiesen, Lizenz („LGPL-2.1 mit Zusatzausnahme")
  **aus zweiter Hand** (xbim-README, siehe `LIZENZPRUEFUNG_2026-08-18.md` §3.8), nicht am
  OCCT-Original.
- **Die Versionen sind die von heute.** `torch` 2.13.0, `numpy` 2.5.2 auf PyPI (lokal
  installiert ist 2.4.6), `Pillow` 12.3.0, `triton` 3.7.1. Nichts davon ist im Projekt
  gepinnt — `pyproject.toml` hat keine Laufzeitabhängigkeiten, und in `auftraege/` steht
  keine Installationsanweisung. **Eine Lizenzprüfung ohne Version ist eine Momentaufnahme**
  (§7, Punkt 3).

---

## 7 · Was daraus folgt — beschrieben, nicht gebaut

Alles Folgende ist **Owner-Entscheid**. Es wurde nichts geändert ausser dieser Datei und
dem Abschnitt „Wissensschulden" in `docs/PLAN.md`.

**1 · Das `NOTICE` ist unvollständig und sollte ergänzt werden.**
Es nennt Blender, IfcOpenShell, CGAL und trimesh. Es nennt nicht:

- **GEOS (LGPL-2.1)** — über shapely in `.venv-ifc`. Das ist die einzige echte
  *Bringschuld* dieses Berichts: Die LGPL-Präzisierung in `CLAUDE.md` verlangt wörtlich,
  dass die Bibliothek „mit ihrer Lizenz ins `NOTICE`" gehört, und für GEOS steht sie dort
  nicht.
- **libquadmath (LGPL-2.1+)** — über numpy, in **beiden** venvs. Gleiche Auflage.
- **libgomp und libgfortran (GPL-3.0-or-later WITH GCC-exception-3.1)** — sinnvollerweise
  mit dem Hinweis, dass die Ausnahme greift, damit ein späterer Prüfer nicht erschrickt.
- **Open CASCADE, GMP, MPFR, Eigen (MPL-2.0), Boost, HDF5, libxml2** — die übrigen
  statischen Bestandteile des IfcOpenShell-Wheels.
- **FreeType** mit der ausdrücklichen Wahl der FTL und deren Nennungsauflage.
- **Die NVIDIA-Laufzeit** als proprietäre Voraussetzung. Sie wird von uns nicht
  ausgeliefert, sondern von pip installiert — aber ein öffentliches Repo, das ohne sie
  nicht rendert, sollte das sagen.

**2 · Eine Architekturänderung ist nicht nötig.** Das ist das eigentliche Ergebnis. Jeder
Fund liegt entweder hinter einer bereits gezogenen Grenze (CGAL, GEOS) oder ist durch eine
Ausnahmeklausel entschärft (libgomp, libgfortran) oder gar nicht erst im Prozess
(FriBidi). **Kein Fund verlangt, `torch` oder `Pillow` in ein eigenes venv zu verschieben.**
Wäre `libgomp` ohne die GCC-Ausnahme gekommen, sähe das anders aus — dann wäre der Ausweg
derselbe wie zweimal zuvor: ein eigenes Environment und ein Subprozessaufruf.

**3 · Zwei Dinge, die man festschreiben sollte, weil sie sonst wegdriften:**

- **Versionen pinnen, bevor ausgeliefert wird.** Dieser Bericht gilt für `torch` 2.13.0
  und `triton` 3.7.1. Ein Wheel kann in der nächsten Fassung eine andere Bibliothek
  bündeln, ohne dass sich die deklarierte Lizenz ändert — genau das ist ja der Befund.
  Ohne Pin ist diese Prüfung in drei Monaten wertlos.
- **CPU-Variante als saubere Rückfallebene notieren.** `torch` von
  `https://download.pytorch.org/whl/cpu` zieht **keine** NVIDIA-Pakete nach. Für alles,
  was ohne GPU läuft (Tests, Trockenläufe, die gesamte QA-Kette), ist das die Variante
  ohne proprietären Anteil. Das ist keine Empfehlung gegen CUDA auf der HomeStation,
  sondern ein Hinweis, dass die Entwicklungsumgebung ihn nicht braucht.

**4 · Falls OpenCV je hinzukommt: `opencv-python-headless`, nicht `opencv-python`** (§5).
Spart eine LGPL-3-Bibliothek (Qt 5) und passt zu Regel 4.

**5 · Die Methodenlehre, in einem Satz:** *Die Kurzangabe eines Wheels ist ein Hinweis,
das Verzeichnis `dist-info/licenses/` ist eine Aussage, und das Verzeichnis `*.libs/` ist
die Wahrheit.* Bei numpy, torch, triton, cryptography und opencv-python wichen alle drei
voneinander ab — fünfmal in fünf von fünf geprüften Fällen mit relevantem Binäranteil.

---

## Quellen

Alle URLs in den Tabellen oben, alle abgerufen am **2026-08-18** über den Agent-Proxy,
ohne Zwischenschaltung einer Suchmaschine.

Abrufwege:
- **Installierte Dateien** unter `/home/user/ai-imaging-in-a-box/.venv-ifc/lib/python3.11/site-packages/`
  (`dist-info/METADATA`, `dist-info/licenses/`, `*.libs/`, `_ifcopenshell_wrapper…so`),
  ausgewertet mit `strings`, `readelf -d`, `nm -D`.
- **PyPI-Metadaten** `https://pypi.org/pypi/<paket>/json`.
- **Wheel-Inhalte ohne Installation**: HTTP-Range-Abrufe auf
  `https://files.pythonhosted.org/packages/…`, ZIP-Zentralverzeichnis und einzelne
  Lizenzdateien; kleine Wheels (`nvidia-cuda-runtime`, `nvidia-nvtx`, `Pillow`,
  `cryptography`) vollständig heruntergeladen.
- **Quellköpfe beim Urheber**: `https://raw.githubusercontent.com/gcc-mirror/gcc/master/…`
  (`COPYING.RUNTIME`, `libgomp/libgomp.h`, `libgfortran/libgfortran.h`,
  `libquadmath/quadmath.h`), `https://raw.githubusercontent.com/CGAL/cgal/master/…`
  (paketweise `license.txt`), `https://raw.githubusercontent.com/huggingface/…/LICENSE`.

Nicht erreichbar über diesen Weg: `github.com` und `api.github.com` (HTTP 403 am Proxy),
`www.cgal.org` (HTTP 403), `gmplib.org` (Verbindungsabbruch), `www.gnu.org`
(Verbindungsabbruch — der Text der GCC-Ausnahme wurde stattdessen aus dem GCC-Quellbaum
gelesen).
