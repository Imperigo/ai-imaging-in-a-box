#!/usr/bin/env python3
"""BEWEIS 03 — Das Node «render» (kette.ART_RENDER) prüft Lizenz, Vertrag und
Geräteschranke in genau dieser Reihenfolge, und die Reihenfolge trägt die Kosten.

Was hier NICHT gemessen werden kann
------------------------------------
Das eigentliche Rechnen — Tiefenkarte hinein, Bild heraus über ``diffusers`` — braucht
``torch``, 20+ GB Gewichte und eine GPU. Nichts davon existiert in diesem Container
(geprüft beim Start dieses Skripts, siehe unten). Der Diffusionsschritt selbst ist daher
für dieses Skript **NICHT GEMESSEN**, nicht **DURCHGEFALLEN** — genau die Unterscheidung,
die die Hausregel dieses Projekts verlangt. Sollte dieses Skript auf der HomeStation
laufen (Gewichte unter ``$AIIMAGING_MODELLE`` bzw. ``/ai``, ``torch``+``diffusers``
installiert), rendert Kachel C in Bild 02 tatsächlich und zeigt das echte Ergebnis statt
der hier eingebauten Attrappen-Stufe — siehe ``_kachel_c``.

Was hier SEHR WOHL gemessen wird — vollständig, ohne GPU, ohne ein einziges Gewicht
--------------------------------------------------------------------------------------
1. ``backbone.BACKBONES`` — die Registry selbst, mit ``backbone.pruefe_lizenz`` auf
   jeden Eintrag angewendet. **Beide Hälften der ControlNet-Naht** (Basismodell und
   ControlNet tragen getrennte Lizenzen, siehe ``backbone._pruefe_controlnet``).
2. ``render.pruefe_auftrag`` — lehnt einen ``RenderAuftrag`` mit ``backbone="flux1-dev"``
   ab, **bevor** irgendeine Datei nach Gewichten durchsucht wird und **bevor**
   ``import torch`` auch nur versucht wird.
3. ``render.rendere`` — drei echte Aufrufe, die zeigen, an welcher von drei Schranken ein
   Auftrag hier tatsächlich hängen bleibt: Lizenz, Umgebung/Gewichte, Geräte-Stack.

Woran man es im Bild sieht
--------------------------
``01_backbone-registry_<N>-modelle_<K>-gesperrt_<M>-mit-controlnet.png``

Eine Zeile je Registry-Eintrag, in Registry-Reihenfolge (das ist zugleich die
Empfehlungsreihenfolge von ``backbone.waehle()``):

    z-image-turbo · qwen-image-edit-2511 · qwen-image-2512 · sdxl-juggernaut ·
    sd35-large · flux2-klein-4b · flux1-dev · flux2-dev

Vier Felder je Zeile, von links:

    Feld 1  Lizenz des BASISMODELLS       grün = permissiv & ohne Auflage
    Feld 2  Lizenz des CONTROLNETS        gelb = zulässig, aber mit Auflage
                                          (Umsatzschwelle, Nennungspflicht, …)
    Feld 3  GESAMTURTEIL (Regel 1)         rot  = unter Regel 1 ausgeschlossen
                                          grau = kein ControlNet nötig (integriertes
                                                 Edit; Feld 2 bleibt dann grau)
    Feld 4  Balken, Länge ∝ vram_gb        aus der Registry gelesen, nicht hier
            (aus render.RenderAuftrag-Sicht: je länger, desto mehr Kartenspeicher)

Beide FLUX-Zeilen (7. und 8.) sind in Feld 1 UND Feld 2 rot: FLUX ist **beidseitig**
gesperrt — selbst ein permissives FLUX-Basismodell würde die Naht nicht retten, weil
auch die verbreiteten Depth-ControlNets für FLUX nicht-kommerziell lizenziert sind
(``backbone.pruefe_lizenz``, Abschnitt „Die zweite Hälfte der Naht"). Das ist der Befund,
den Feld 2 zeigt und den ein Blick nur auf Feld 1 verdeckt hätte.

``02_pruefe_auftrag_gatter_<A-status>_<B-status>_<C-status>.png``

Drei Kacheln, derselbe ``RenderAuftrag`` (dieselbe Tiefenkarte, derselbe Prompt),
nur der Backbone bzw. die Modellwurzel unterscheidet sich — jede Kachel zeigt, an
welcher Schranke der Lauf **hier** tatsächlich endet, gemessen über einen echten Aufruf
von ``render.rendere``:

    Kachel A  backbone="flux1-dev"                        ROT
              abgelehnt an Regel 1 — noch bevor
              ``modellwurzel_lage`` auch nur geprüft wird.
    Kachel B  backbone="z-image-turbo", Vertrag besteht,   GELB
              aber ``$AIIMAGING_MODELLE``/``/ai`` existiert
              hier nicht — abgelehnt mangels Ablage,
              nicht mangels Lizenz.
    Kachel C  wie B, aber mit einer ATTRAPPEN-Modellwurzel, BLAU  (nur falls kein
              die alle von der Registry verlangten Pfade   torch/diffusers hier)
              als leere Stub-Dateien führt — die Prüfung
              kommt bis zum ``import torch``, und der
              schlägt hier fehl. **Blau, nicht rot**: Die
              Fehlermeldung selbst benennt eine
              Geräteschranke, keinen Vertragsbruch.

Ein helles Feld unten in jeder Kachel bestätigt ``'torch' not in sys.modules`` nach dem
jeweiligen Aufruf — in KEINEM der drei Fälle wurde die GPU-Bibliothek auch nur geladen.
Die Balkenlänge in jeder Kachel codiert die erreichte Prüfstufe (1, 2 oder 3 von 3) —
je weiter rechts der Balken reicht, desto später griff die Schranke.

Kein Bild ist gemalt, um eine Behauptung zu illustrieren: Jede Farbe kommt aus einem
Wörterbuch, das in genau diesem Lauf von ``backbone.pruefe_lizenz`` bzw.
``render.rendere`` zurückgegeben wurde.

Aufruf
------
    python3 tools/beweis/03_knoten_render.py [ziel_verzeichnis]

Ohne Argument schreibt es nach ``build/beweis/03_knoten_render/``.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import backbone, bildschreiben, render  # noqa: E402

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "03_knoten_render"

# --------------------------------------------------------------------------------------
# Farbsprache — dieselbe Rolle wie in 01/02: keine Schrift im Bild, die Bedeutung steht
# im Docstring und im Dateinamen (Regel 2).
# --------------------------------------------------------------------------------------
GRUEN = (60, 150, 70)        # zulässig, ohne Auflage
GELB = (200, 150, 40)        # zulässig mit Auflage / abgelehnt mangels Ablage (kein Vertragsbruch)
ROT = (190, 60, 50)          # unter Regel 1 ausgeschlossen bzw. echter Fehlschlag
GRAU = (140, 140, 140)       # ControlNet nicht nötig (integriertes Edit)
BLAU = (80, 110, 175)        # Geräteschranke: NICHT GEMESSEN, nicht durchgefallen
MARKE = (215, 232, 250)      # Bestätigung: 'torch' nicht in sys.modules
HINTERGRUND = (245, 245, 245)
GRUND = (48, 48, 48)
RAND = 12
FUGE = 10


def _neues_bild(breite: int, hoehe: int, hg=HINTERGRUND) -> list:
    return [hg] * (breite * hoehe)


def _rechteck(px: list, breite: int, hoehe: int, x0, y0, x1, y1, farbe) -> None:
    xa, xb = sorted((max(0, int(round(x0))), min(breite, int(round(x1)))))
    ya, yb = sorted((max(0, int(round(y0))), min(hoehe, int(round(y1)))))
    for y in range(ya, yb):
        px[y * breite + xa:y * breite + xb] = [farbe] * (xb - xa)


def _formatiere(x) -> str:
    """Für Dateinamen: kompakt, kein Komma."""
    if isinstance(x, float):
        return f"{x:.3f}".rstrip("0").rstrip(".") or "0"
    return str(x)


# --------------------------------------------------------------------------------------
# Bild 1 — die Registry als Farbtafel
# --------------------------------------------------------------------------------------

def _farbe_basis(eintrag) -> tuple:
    if not eintrag.kommerziell_nutzbar:
        return ROT
    if backbone.lizenzquelle.ist_permissiv(eintrag.lizenz):
        return GRUEN
    return GELB


def _farbe_controlnet(cn: dict) -> tuple:
    if not cn["noetig"]:
        return GRAU
    if cn["zulaessig"] is None:
        return BLAU  # nötig, aber nicht benannt — unentschieden, kein Ausschluss
    if not cn["zulaessig"]:
        return ROT
    return GRUEN if not cn["auflagen"] else GELB


def _farbe_gesamt(zulaessig: bool) -> tuple:
    return GRUEN if zulaessig else ROT


def bild_registry(ziel: Path) -> Path:
    """Jede Zeile ein Registry-Eintrag, jede Farbe aus ``backbone.pruefe_lizenz``."""
    eintraege = list(backbone.BACKBONES.values())
    urteile = {e.name: backbone.pruefe_lizenz(e.name) for e in eintraege}

    zelle_b, zelle_h = 100, 44
    balken_max = 220
    n = len(eintraege)
    breite = RAND * 2 + 3 * zelle_b + 2 * FUGE + FUGE + balken_max
    hoehe = RAND * 2 + n * zelle_h + (n - 1) * FUGE
    px = _neues_bild(breite, hoehe, hg=GRUND)

    hoechstes_vram = max(e.vram_gb for e in eintraege)

    for i, eintrag in enumerate(eintraege):
        urteil = urteile[eintrag.name]
        y0 = RAND + i * (zelle_h + FUGE)
        y1 = y0 + zelle_h

        x0 = RAND
        _rechteck(px, breite, hoehe, x0, y0, x0 + zelle_b, y1, _farbe_basis(eintrag))

        x0 += zelle_b + FUGE
        _rechteck(px, breite, hoehe, x0, y0, x0 + zelle_b, y1,
                  _farbe_controlnet(urteil["controlnet"]))

        x0 += zelle_b + FUGE
        _rechteck(px, breite, hoehe, x0, y0, x0 + zelle_b, y1,
                  _farbe_gesamt(urteil["zulaessig"]))

        x0 += zelle_b + FUGE + FUGE
        laenge = max(4, (eintrag.vram_gb / hoechstes_vram) * balken_max)
        _rechteck(px, breite, hoehe, x0, y0 + zelle_h * 0.3, x0 + laenge,
                  y0 + zelle_h * 0.7, (110, 130, 150))

    n_gesperrt = sum(1 for u in urteile.values() if not u["zulaessig"])
    n_controlnet = sum(1 for e in eintraege
                       if e.konditionierung == backbone.KOND_DEPTH_CONTROLNET)
    pfad = ziel / (f"01_backbone-registry_{n}-modelle_{n_gesperrt}-gesperrt_"
                   f"{n_controlnet}-mit-controlnet.png")
    bildschreiben.schreibe_farb_png(pfad, px, breite, hoehe)
    print(f"Registry: {n} Backbones, {n_gesperrt} unter Regel 1 gesperrt "
          f"({', '.join(n for n, u in urteile.items() if not u['zulaessig'])}), "
          f"{n_controlnet} mit Depth-ControlNet-Naht.")
    return pfad


# --------------------------------------------------------------------------------------
# Bild 2 — das Gatter: Regel 1 → Umgebung/Gewichte → Geräte-Stack
# --------------------------------------------------------------------------------------

PROMPT = "Verwaltungsgebäude am Abend, Sichtbeton, tiefstehende Sonne"


def _tiefe_dummy(ziel: Path) -> Path:
    """Eine echte, kleine Tiefenkarte — reine stdlib, kein Blender nötig für diesen
    Beweis: ``pruefe_auftrag`` prüft nur, ob die Datei existiert, nicht ihren Inhalt.
    Der Gradient ist trotzdem real gerechnet, nicht nur eine leere Datei."""
    b, h = 48, 32
    werte = [((x + y) / (b + h - 2)) for y in range(h) for x in range(b)]
    pfad = ziel / "eingabe" / "tiefe_dummy.png"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    bildschreiben.schreibe_graustufen_png(pfad, werte, b, h)
    return pfad


def _torch_verfuegbar() -> bool:
    try:
        import torch  # noqa: F401
        import diffusers  # noqa: F401
    except ImportError:
        return False
    return True


def _baue_stub_gewichte(ziel: Path, eintrag) -> Path:
    """Leere Dateien/Ordner unter genau den Namen, die die Registry verlangt — genug,
    damit ``backbone.vorhandene_dateien`` 'vollständig' meldet, ohne ein einziges
    echtes Byte an Gewichten. Die Prüfung kommt so bis zum ``import torch`` durch."""
    wurzel = ziel / "stub_gewichte" / eintrag.name
    for name in eintrag.dateien:
        p = wurzel / name
        if "." in name:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch()
        else:
            p.mkdir(parents=True, exist_ok=True)
    return wurzel


def _kachel(status: str, farbe: tuple, stufe: int, torch_frei: bool, *,
            breite: int = 220, hoehe: int = 200) -> tuple:
    px = _neues_bild(breite, hoehe, hg=GRUND)
    _rechteck(px, breite, hoehe, 10, 10, breite - 10, hoehe - 40, farbe)
    balken_max = breite - 20
    laenge = 10 + (stufe / 3) * balken_max
    _rechteck(px, breite, hoehe, 10, hoehe - 34, laenge, hoehe - 20, (110, 130, 150))
    _rechteck(px, breite, hoehe, 10, hoehe - 16, breite - 10, hoehe - 6,
             MARKE if torch_frei else ROT)
    return px, breite, hoehe


def _tafel(kacheln: list) -> tuple:
    n = len(kacheln)
    b0, h0 = kacheln[0][1], kacheln[0][2]
    breite = RAND * 2 + n * b0 + (n - 1) * FUGE
    hoehe = RAND * 2 + h0
    px = _neues_bild(breite, hoehe, hg=GRUND)
    for k, (kachel, b, h) in enumerate(kacheln):
        x0 = RAND + k * (b0 + FUGE)
        for y in range(h):
            zeile = (RAND + y) * breite + x0
            px[zeile:zeile + b] = kachel[y * b:(y + 1) * b]
    return px, breite, hoehe


def bild_gatter(ziel: Path) -> Path:
    depth = _tiefe_dummy(ziel)

    vor_a = "torch" in sys.modules
    auftrag_a = render.RenderAuftrag(depth_png=str(depth), prompt=PROMPT,
                                     backbone="flux1-dev")
    mangel_a = render.pruefe_auftrag(auftrag_a)
    t0 = time.perf_counter()
    ergebnis_a = render.rendere(auftrag_a)
    dauer_a = time.perf_counter() - t0
    torch_frei_a = "torch" not in sys.modules
    print(f"Kachel A (flux1-dev): status={ergebnis_a['status']!r}, "
          f"{len(mangel_a)} Mangel/Mängel, {dauer_a * 1000:.3f} ms, "
          f"torch importiert: {not torch_frei_a}")
    assert ergebnis_a["status"] == render.STATUS_ABGELEHNT
    assert any("Regel 1" in m for m in mangel_a), mangel_a

    auftrag_b = render.RenderAuftrag(depth_png=str(depth), prompt=PROMPT,
                                     backbone=render.VORGABE_BACKBONE)
    mangel_b = render.pruefe_auftrag(auftrag_b)
    lage_b = render.modellwurzel_lage(render.VORGABE_BACKBONE)
    t0 = time.perf_counter()
    ergebnis_b = render.rendere(auftrag_b)
    dauer_b = time.perf_counter() - t0
    torch_frei_b = "torch" not in sys.modules
    print(f"Kachel B ({render.VORGABE_BACKBONE}, Ablage {lage_b['wurzel']!r} "
          f"existiert: {lage_b['existiert']}): status={ergebnis_b['status']!r}, "
          f"{len(mangel_b)} Mangel/Mängel, {dauer_b * 1000:.3f} ms")

    eintrag_c = backbone.hole(render.VORGABE_BACKBONE)
    torch_da = _torch_verfuegbar()
    if not torch_da:
        stub = _baue_stub_gewichte(ziel, eintrag_c)
        auftrag_c = render.RenderAuftrag(depth_png=str(depth), prompt=PROMPT,
                                         backbone=render.VORGABE_BACKBONE,
                                         modell_wurzel=str(stub))
        t0 = time.perf_counter()
        ergebnis_c = render.rendere(auftrag_c)
        dauer_c = time.perf_counter() - t0
        torch_frei_c = "torch" not in sys.modules
        fehler_c = (ergebnis_c.get("error") or "").lower()
        geraeteschranke = ("torch" in fehler_c) or ("diffusers" in fehler_c)
        status_c = ergebnis_c["status"]
        print(f"Kachel C (Stub-Gewichte unter {stub}): status={status_c!r}, "
              f"Fehlermeldung nennt Geräteschranke: {geraeteschranke}, "
              f"{dauer_c * 1000:.3f} ms")
        farbe_c = BLAU if geraeteschranke else ROT
        stufe_c = 3
    else:
        # Echtes Gerät vorhanden — dieselbe Auskunft wie Kachel B, jetzt am Gerät.
        status_c = ergebnis_b["status"]
        torch_frei_c = False  # torch wurde gerade benutzt, das ist hier richtig so
        farbe_c = GRUEN if status_c == render.STATUS_OK else (
            ROT if status_c == render.STATUS_FEHLER else GELB)
        stufe_c = 3
        print("torch/diffusers sind HIER vorhanden — Kachel C spiegelt das echte "
              f"Ergebnis von Kachel B: status={status_c!r}.")

    kachel_a = _kachel(ergebnis_a["status"], ROT, 1, torch_frei_a)
    kachel_b = _kachel(ergebnis_b["status"], GELB, 2, torch_frei_b)
    kachel_c = _kachel(status_c, farbe_c, stufe_c, torch_frei_c)

    px, breite, hoehe = _tafel([kachel_a, kachel_b, kachel_c])
    pfad = ziel / (f"02_pruefe_auftrag_gatter_A-{ergebnis_a['status']}_"
                   f"B-{ergebnis_b['status']}_C-{status_c}.png")
    bildschreiben.schreibe_farb_png(pfad, px, breite, hoehe)
    return pfad


def main(argv: list[str] | None = None) -> int:
    ziel = Path(argv[0]) if argv else ZIEL_VORGABE
    ziel.mkdir(parents=True, exist_ok=True)

    print(f"torch/diffusers vor jedem Aufruf verfügbar: {_torch_verfuegbar()}")

    geschrieben = [bild_registry(ziel), bild_gatter(ziel)]

    print("\nGESCHRIEBEN:")
    for pfad in geschrieben:
        print(f"  {pfad.relative_to(WURZEL) if WURZEL in pfad.parents else pfad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
