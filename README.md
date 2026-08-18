# ai-imaging-in-a-box

Vertiefungsarbeit ETH Zürich · HS26 · ITA · Betreuung Gonzalo Casas

Ein lokal lauffähiges, knotenbasiertes Framework für geometrie-treue KI-Architektur-
Visualisierung: IFC-Geometrie hinein, verifizierte Bilder heraus — ohne Cloud, mit
austauschbarem lokalem Bildmodell.

**Status:** Vorbereitung. Es ist noch nichts gebaut.

- [`docs/LAGEBEURTEILUNG_2026-08-14.md`](docs/LAGEBEURTEILUNG_2026-08-14.md) —
  Bestandsaufnahme der offenen Bausteine mit Lizenzprüfung
- [`docs/EINBINDUNG_KOSMOORBIT_2026-08-14.md`](docs/EINBINDUNG_KOSMOORBIT_2026-08-14.md) —
  der MCP-Vertrag gegenüber KosmoOrbit und was er für die Bauform bedeutet
- [`docs/LEXIKON.md`](docs/LEXIKON.md) — Fachbegriffe aus Softwareentwicklung, Lizenzrecht
  und KI, erklärt für Leser:innen mit Architekturhintergrund
- [`docs/PLAN.md`](docs/PLAN.md) — Vorgehensplan, Phasen 0–4, offene Wissensschulden
- [`docs/sitzungen/`](docs/sitzungen/) — Sitzungsprotokolle: Entscheidungen und Begründungen
- [`CLAUDE.md`](CLAUDE.md) — die vier nicht verhandelbaren Regeln

## Entwicklung

Voraussetzung: Python 3.11 oder neuer. Der Kern hat keine Laufzeitabhängigkeiten.

**Testgeometrie erzeugen.** Das Repo enthält keine IFC-Datei — sie wird erzeugt (Regel 3):

```
python3 tools/make_test_ifc.py build/testbau.ifc
```

**Environment hinter der Prozessgrenze anlegen.** `ifcopenshell` steht unter LGPL und
bringt GPL-Anteile mit. Deshalb liegt es in einem *eigenen* Environment und wird als
Subprozess aufgerufen, nie in den Kern importiert:

```
python3 -m venv .venv-ifc && .venv-ifc/bin/pip install ifcopenshell trimesh numpy
```

**Tests laufen lassen:**

```
python3 -m pytest
```

**Umgebungsvariablen.** Beide zeigen auf Programme jenseits der Prozessgrenze; ohne sie
wird an den üblichen Orten gesucht:

- `AIIMAGING_IFC_PYTHON` — der Python-Interpreter des IFC-Environments,
  Rückfall ohne Variable: `.venv-ifc/bin/python`
- `AIIMAGING_BLENDER` — das Blender-Binary; ohne Variable wird `blender` im PATH gesucht

## Lizenz

Apache-2.0 — siehe [`LICENSE`](LICENSE).
