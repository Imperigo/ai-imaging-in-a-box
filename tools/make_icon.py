"""Das Visbox-Icon (Owner-Entscheid 88, 14.10.2026, Blatt 20 Vorschlag A «Box mit Bild").

Ein Gebäude als Box, eine Seite ist schon Bild (blau): Modell hinein, Bild heraus. Gezeichnet
ohne Schrift, damit es überall gleich aussieht. Farben aus der Visbox-Oberfläche.

Erzeugt nach ``ipad/Marke/``:

* ``visbox-icon.svg`` — die Vorlage, randlos (iPad: iOS legt die Ecken selbst darüber);
* ``visbox-icon-mac.svg`` — dieselbe Zeichnung im abgerundeten Feld mit Rand, wie macOS-Icons
  seit Big Sur gezeichnet werden (824 von 1024 Punkten, mittig);
* mit ``--png`` (braucht Chromium, liegt am Heim-PC wie hier unter ``/opt/pw-browsers``) die
  PNG-Stufen, ``AppIcon.appiconset`` fürs iPad und ``Visbox.icns`` für den Mac — ``.icns`` wird
  mit der Standardbibliothek geschrieben (ein Behälter aus PNG-Blöcken, Apple «icns»-Format).

Eigene Zeichnung, Apache-2.0 wie das Repo.
"""
from __future__ import annotations

import argparse
import json
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]

GRUND = "#12161c"
LINIE = "#e8eaed"
BILD = "#2f6fd6"
KURVE = "#bcd3ff"

#: Die Zeichnung auf 1024 × 1024, ohne Grund.
ZEICHNUNG = f"""
  <path d="M512 210 L790 360 L790 664 L512 814 L234 664 L234 360 Z" fill="none" stroke="{LINIE}" stroke-width="34" stroke-linejoin="round"/>
  <path d="M234 360 L512 510 L790 360 M512 510 L512 814" fill="none" stroke="{LINIE}" stroke-width="34" stroke-linejoin="round"/>
  <path d="M512 510 L790 360 L790 664 L512 814 Z" fill="{BILD}"/>
  <path d="M560 700 L640 610 L700 660 L760 580" fill="none" stroke="{KURVE}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>
"""


def svg_randlos() -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" '
            f'viewBox="0 0 1024 1024">\n  <rect width="1024" height="1024" fill="{GRUND}"/>'
            f"{ZEICHNUNG}</svg>\n")


def svg_mac() -> str:
    # 824er Feld mittig, Ecken 185 (≈ 22.5 %), die Zeichnung auf 80 % verkleinert.
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" '
            f'viewBox="0 0 1024 1024">\n  <rect x="100" y="100" width="824" height="824" '
            f'rx="185" fill="{GRUND}"/>\n  <g transform="translate(512 512) scale(0.8) '
            f'translate(-512 -512)">{ZEICHNUNG}</g>\n</svg>\n')


def _chromium() -> str:
    for p in ("/opt/pw-browsers/chromium/chrome-linux/chrome", "/opt/pw-browsers/chromium"):
        if Path(p).is_file():
            return p
    kandidaten = sorted(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome"))
    if kandidaten:
        return str(kandidaten[-1])
    gefunden = shutil.which("chromium") or shutil.which("chromium-browser")
    if not gefunden:
        raise SystemExit("Chromium nicht gefunden — PNG lassen sich nur mit ihm erzeugen.")
    return gefunden


def _rastere(svg: str, ziel: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        seite = Path(tmp) / "icon.html"
        seite.write_text("<!doctype html><html><head><style>html,body{margin:0;background:"
                         "transparent}svg{display:block}</style></head><body>" + svg
                         + "</body></html>", encoding="utf-8")
        subprocess.run([_chromium(), "--headless", "--no-sandbox", "--disable-gpu",
                        "--hide-scrollbars", "--force-device-scale-factor=1",
                        # HOEHER ALS NOETIG, dann zugeschnitten: Headless-Chromium zieht von
                        # der Fensterhoehe etwas ab, und unten bliebe ein schwarzer Streifen.
                        "--default-background-color=00000000", "--window-size=1024,1400",
                        f"--screenshot={ziel}", seite.as_uri()],
                       check=True, capture_output=True, timeout=120)
    from PIL import Image
    with Image.open(ziel) as bild:
        bild.crop((0, 0, 1024, 1024)).save(ziel)


def _verkleinere(quelle: Path, ziel: Path, kante: int) -> None:
    from PIL import Image                                   # nur zum Erzeugen, nie im Kern
    with Image.open(quelle) as bild:
        bild.resize((kante, kante), Image.LANCZOS).save(ziel)


#: icns-Blocktypen mit PNG-Inhalt (Apple: ic07 128, ic08 256, ic09 512, ic10 1024 (@2x 512),
#: ic11 32 (@2x 16), ic12 64 (@2x 32), ic13 256 (@2x 128), ic14 512 (@2x 256)).
ICNS_BLOECKE = (("ic11", 32), ("ic12", 64), ("ic07", 128), ("ic13", 256), ("ic08", 256),
                ("ic14", 512), ("ic09", 512), ("ic10", 1024))


def schreibe_icns(pngs: dict[int, bytes], ziel: Path) -> None:
    bloecke = b"".join(art.encode("ascii") + struct.pack(">I", 8 + len(pngs[kante]))
                       + pngs[kante] for art, kante in ICNS_BLOECKE)
    ziel.write_bytes(b"icns" + struct.pack(">I", 8 + len(bloecke)) + bloecke)


def main(argv=None, *, wurzel: Path = WURZEL) -> int:
    """``wurzel``: wohin geschrieben wird (das Repo; die Proben geben einen leeren Ordner)."""
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--png", action="store_true", help="auch PNG, appiconset und icns")
    args = a.parse_args(argv)
    ziel = Path(wurzel) / "ipad" / "Marke"
    ziel.mkdir(parents=True, exist_ok=True)
    (ziel / "visbox-icon.svg").write_text(svg_randlos(), encoding="utf-8")
    (ziel / "visbox-icon-mac.svg").write_text(svg_mac(), encoding="utf-8")
    if not args.png:
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        _rastere(svg_randlos(), t / "ipad.png")
        _rastere(svg_mac(), t / "mac.png")
        # iPad: EIN Bild 1024, ohne Durchsicht (App Store und Xcode verlangen das).
        from PIL import Image
        satz = Path(wurzel) / "ipad" / "Visbox.swiftpm" / "Assets.xcassets" / "AppIcon.appiconset"
        satz.mkdir(parents=True, exist_ok=True)
        with Image.open(t / "ipad.png") as bild:
            bild.convert("RGB").save(satz / "AppIcon-1024.png")
        (satz / "Contents.json").write_text(json.dumps({
            "images": [{"filename": "AppIcon-1024.png", "idiom": "universal",
                        "platform": "ios", "size": "1024x1024"}],
            "info": {"author": "xcode", "version": 1}}, indent=2) + "\n", encoding="utf-8")
        (satz.parent / "Contents.json").write_text(json.dumps(
            {"info": {"author": "xcode", "version": 1}}, indent=2) + "\n", encoding="utf-8")
        # Mac: icns aus den Stufen.
        pngs = {}
        for kante in sorted({k for _, k in ICNS_BLOECKE}):
            stufe = t / f"mac-{kante}.png"
            _verkleinere(t / "mac.png", stufe, kante)
            pngs[kante] = stufe.read_bytes()
        mac = Path(wurzel) / "ipad" / "VisboxMac" / "App"
        mac.mkdir(parents=True, exist_ok=True)
        schreibe_icns(pngs, mac / "Visbox.icns")
        shutil.copyfile(t / "mac.png", ziel / "visbox-icon-mac-1024.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
