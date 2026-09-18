#!/usr/bin/env python3
"""Packt die Beweisbilder als **Ordner zum Herunterladen** — mit dem Text daneben.

Warum es dieses Werkzeug gibt
-----------------------------
Die Galerie (`tools/beweisgalerie.py`) ist eine Seite: schön zu lesen, aber nichts, was
man weiterreicht, in eine Arbeit einfügt oder offline durchblättert. Wer die Bilder
einzeln braucht, bekam bisher den Hinweis «liegen unter `build/beweis/`» — und dort liegen
sie ohne den Satz, der sagt, was man sieht.

*Ein Bild ohne den Satz daneben ist Dekoration* — derselbe Grund wie bei der Galerie, nur
für den Fall, dass jemand die Dateien in der Hand hat und nicht die Seite.

Was es tut
----------
Je Tafel ein Ordner, darin die Bilder **und** eine ``LIESMICH.md`` mit Titel, dem Satz aus
:data:`aiimaging-galerie.TAFELN` und dem Vorbehalt, falls einer dransteht. Obendrauf ein
Verzeichnis über alles. Auf Wunsch als ``.zip``.

Was es NICHT tut
----------------
Es nimmt **nur die kuratierten Tafeln**, also die flachen PNG je Ordner — nicht das, was
in Arbeitsordnern wie ``lauf/`` oder ``_arbeit/`` liegt. Das sind Rohausgaben von Blender,
die beim Lauf anfallen; sie tragen keinen Namen, der etwas aussagt, und keine
Bildunterschrift. Wer sie will, findet sie in ``build/beweis/``.

Und es **erfindet keine Tafel**: Zu jedem Ordner muss ein Eintrag in ``TAFELN`` stehen,
sonst hält der Lauf an — dieselbe Regel wie in der Galerie und aus demselben Grund.

Aufruf:
    python3 tools/beweispaket.py                      # nach build/beweispaket/
    python3 tools/beweispaket.py --zip                # dazu build/beweispaket.zip
    python3 tools/beweispaket.py --nach /wohin --zip
"""
from __future__ import annotations

import argparse
import importlib.util
import shutil
import sys
import zipfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]


def _galerie():
    """Das Galerie-Modul laden, um **eine** Quelle für Titel und Texte zu haben.

    Die Texte hier zu wiederholen wäre die zweite Wahrheit, die beim nächsten Zusatz
    auseinanderläuft — und zwar unbemerkt, weil beide für sich richtig aussehen.
    """
    spec = importlib.util.spec_from_file_location(
        "beweisgalerie", Path(__file__).resolve().parent / "beweisgalerie.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _liesmich_tafel(titel: str, marke, was: str, vorbehalt, bilder, gewaehlt) -> str:
    zeilen = [f"# {titel}", ""]
    if marke:
        zeilen += [f"**Gemessen mit:** {marke}", ""]
    zeilen += [was.replace("<code>", "`").replace("</code>", "`"), ""]
    if vorbehalt:
        zeilen += ["> **Vorbehalt.** "
                   + vorbehalt.replace("<code>", "`").replace("</code>", "`"), ""]
    zeilen += [f"## {len(bilder)} Bilder", ""]
    for b in bilder:
        marke_v = "  · **im Vortrag**" if b.name in gewaehlt else ""
        zeilen.append(f"* `{b.name}`{marke_v}")
    zeilen += ["", "*Die Dateinamen tragen die Messwerte — sie sind die Bildunterschrift.*"]
    return "\n".join(zeilen) + "\n"


def packe(nach: Path, *, bilderwurzel: Path | None = None) -> tuple[int, int, int]:
    """Alles nach ``nach`` schreiben. Zurück kommt ``(Tafeln, Bilder, im Vortrag)``."""
    g = _galerie()
    wurzel = Path(bilderwurzel) if bilderwurzel else g.BILDER
    if not wurzel.is_dir():
        raise SystemExit(f"{wurzel} gibt es nicht — erst `python3 tools/beweise_fahren.py`.")

    ordner = sorted(p for p in wurzel.iterdir()
                    if p.is_dir() and not p.name.startswith("_"))
    unbekannt = [p.name for p in ordner if p.name not in g.TAFELN]
    if unbekannt:
        raise SystemExit("Ohne Text keine Tafel — kein Eintrag in TAFELN für:\n  "
                         + "\n  ".join(unbekannt))

    vortrag = g._vortragsbilder()
    nach = Path(nach)
    if nach.exists():
        shutil.rmtree(nach)
    nach.mkdir(parents=True)

    verzeichnis, n_bilder, n_wahl = [], 0, 0
    for nr, p in enumerate(ordner, 1):
        titel, marke, was, vorbehalt = g.TAFELN[p.name]
        bilder = sorted(p.glob("*.png"))          # NUR die kuratierten, siehe Modultext
        gewaehlt = {b.name for b in bilder if (p.name, b.name) in vortrag}
        ziel = nach / p.name
        ziel.mkdir()
        for b in bilder:
            shutil.copy2(b, ziel / b.name)
        (ziel / "LIESMICH.md").write_text(
            _liesmich_tafel(titel, marke, was, vorbehalt, bilder, gewaehlt),
            encoding="utf-8")
        n_bilder += len(bilder)
        n_wahl += len(gewaehlt)
        verzeichnis.append((nr, p.name, titel, len(bilder), len(gewaehlt), vorbehalt))

    fehlend = sorted(k for k in g.TAFELN if not (wurzel / k).is_dir())
    (nach / "LIESMICH.md").write_text(
        _liesmich_gesamt(verzeichnis, n_bilder, n_wahl, fehlend, len(g.TAFELN)),
        encoding="utf-8")
    return len(ordner), n_bilder, n_wahl


def _liesmich_gesamt(verzeichnis, n_bilder, n_wahl, fehlend, n_tafeln) -> str:
    zeilen = [
        "# Beweisgang KosmoVis — die Bilder",
        "",
        f"**{len(verzeichnis)} von {n_tafeln} Tafeln · {n_bilder} Bilder · "
        f"{n_wahl} davon im Vortrag**",
        "",
        "Jedes Bild steht für eine Messung. Der Satz daneben sagt, was man sieht — er "
        "steht in der `LIESMICH.md` des jeweiligen Ordners, und die Dateinamen tragen die "
        "Messwerte.",
        "",
        "Erzeugt aus `build/beweis/` mit `python3 tools/beweispaket.py`. Die Bilder liegen "
        "**nicht** im Repo: Sie entstehen neu aus `tools/beweis/*.py`. Ein Bild, das man "
        "nicht neu erzeugen kann, belegt nur, dass es einmal eines gab.",
        "",
        "| | Tafel | Bilder | im Vortrag |",
        "|---|---|---|---|",
    ]
    for nr, name, titel, n, w, _ in verzeichnis:
        zeilen.append(f"| {nr:02d} | **{titel}** <br>`{name}` | {n} | {w or '—'} |")
    mit_vorbehalt = [(nr, titel, v) for nr, _, titel, _, _, v in verzeichnis if v]
    if mit_vorbehalt:
        zeilen += ["", "## Tafeln mit einem Vorbehalt", "",
                   "*Was an ihnen nicht gemessen ist, steht dran — nicht, weil es klein "
                   "wäre, sondern damit niemand es für gemessen hält.*", ""]
        for nr, titel, v in mit_vorbehalt:
            zeilen.append(f"* **{nr:02d} · {titel}** — "
                          + v.replace("<code>", "`").replace("</code>", "`"))
    if fehlend:
        zeilen += ["", "## NICHT GEFAHREN in diesem Lauf", "",
                   "*Weder vorhanden noch «gibt es nicht» — sie haben in diesem Lauf keine "
                   "Bilder geschrieben.*", ""]
        zeilen += [f"* `{k}`" for k in fehlend]
    return "\n".join(zeilen) + "\n"


def zippe(ordner: Path, ziel: Path) -> Path:
    """Den Ordner als ``.zip`` — mit relativen Pfaden, damit er überall auspackt."""
    ziel = Path(ziel)
    with zipfile.ZipFile(ziel, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(Path(ordner).rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(Path(ordner).parent))
    return ziel


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--nach", type=Path, default=WURZEL / "build" / "beweispaket")
    p.add_argument("--bilder", type=Path, default=None,
                   help="Wo die Beweisbilder liegen (Vorgabe: build/beweis)")
    p.add_argument("--zip", action="store_true", help="zusätzlich ein .zip daneben legen")
    a = p.parse_args(argv)

    tafeln, bilder, wahl = packe(a.nach, bilderwurzel=a.bilder)
    print(f"{tafeln} Tafeln, {bilder} Bilder ({wahl} im Vortrag) nach {a.nach}")
    if a.zip:
        z = zippe(a.nach, a.nach.with_suffix(".zip"))
        print(f"{z}  {z.stat().st_size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
