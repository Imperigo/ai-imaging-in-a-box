#!/usr/bin/env python3
"""Erklärkarten für die Tafel: was die iPad-App von Visbox kann — ein eigenes Abteil «Visbox · iPad».

**Wozu** (Owner, 24.10.2026): *«richte bitte parallel auf der kosmo tafel bei visbox abteil ein abteil fürs ipad
ein mit der ui, funktionen etc die auf dem ipad sind, falls noch nichts da ist»*. Bis dahin gab es auf der Tafel
zum iPad nur die Knotenkarte «Sketch from iPad» — nichts über die App selbst. Je Bereich eine Karte: Übersicht,
Koppeln, Verbindungszeile, Zeichenfläche, Ebenen, Senden, Parkfach, Mappe, Bildansicht, Einstellungen und
Fassung, Grenzen mit dem Geplanten.

**Nur was im Code steht.** Jede Bildschirm-Beschriftung, die eine Karte in Klammern nennt, muss wortgleich in
den Quellen unter ``ipad/Visbox.swiftpm`` stehen — die Probe ``tests/test_ipad_tafel.py`` sucht sie dort.
Geplantes steht **nur** im Feld ``geplant`` (eigener, gestrichelter Block «Planned — decided, not built»), mit
dem Entscheid, der es beschliesst; die Probe hält die Wörter auseinander.

**Bilder ohne Gerät.** Hier läuft kein Simulator. Die Bildschirme sind darum **gezeichnete Schemata** (SVG),
beschriftet «Drawn schematic — not a screenshot», mit den Farben, Massen und Beschriftungen aus dem Code
(``Kern/Pruefzeichen.swift`` ``Blattfarbe``, ``Leiste/Zeichenblatt.swift``) — keine erfundenen Teile. Nummern im
Schema verweisen auf die Zeilen rechts.

Regel 100 (Entscheid vom 20.10.2026): Die Karten sind für Leser — sie nennen kein Partnerprogramm und keinen
anderen Worker. Sprache nach Entscheid 142: englisch; die Oberfläche zeigt deutsche Beschriftungen, die in
Klammern hinter dem englischen Begriff stehen.

Die Karten sind **erzeugt, nicht abgelegt** (PNG auf die Tafel, Zweig ``zentrale``, ``tafel/kosmovis/``). Das
Blatt ``docs/IPAD_ERKLAERT.en.md`` wird aus denselben Daten geschrieben (``--markdown``); die Probe hält beide
gleich. Bild: HTML → Chromium ohne Fenster → PNG, zugeschnitten (Werkzeuge aus ``tools/knoten_tafel.py``).

    python tools/ipad_tafel.py --ausgabe <ordner>
    python tools/ipad_tafel.py --ausgabe <ordner> --karte 03
    python tools/ipad_tafel.py --ausgabe <ordner> --nur-html
    python tools/ipad_tafel.py --markdown docs/IPAD_ERKLAERT.en.md
"""
from __future__ import annotations

import argparse
import html
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
QUELLEN = WURZEL / "ipad" / "Visbox.swiftpm"
BLATT = "docs/IPAD_ERKLAERT.en.md"
GRUPPE = "Visbox · iPad"
DATUM = "20261024"


def _knoten_werkzeug():
    """Schrift, Zuschnitt und Chromium aus ``tools/knoten_tafel.py`` — eine Stelle, nicht zwei."""
    pfad = Path(__file__).resolve().parent / "knoten_tafel.py"
    spec = importlib.util.spec_from_file_location("knoten_tafel_fuer_ipad", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


KT = _knoten_werkzeug()
#: Wörter, die auf keiner Karte stehen dürfen (Regel 100) — dieselbe Liste wie bei den Knotenkarten.
VERBOTEN = KT.VERBOTEN

# ── Farben der App (Kern/Pruefzeichen.swift: Blattfarbe, Urteilsfarben; Kern/Stiftfarben.swift) ─────────
GRUND, FELD, LEISTE, BUEHNE = "#14161a", "#1c1f26", "#16191e", "#101317"
LINIE, SCHRIFT, LEISE = "#2b3038", "#e6e8ec", "#9aa2ae"
GEW_RAND, GEW_GRUND = "#4ea373", "#223028"
PAPIER = "#191d23"
STIFT = {"Orange": "#e08b52", "Hell": "#e6e8ec", "Blau": "#6fb3d2", "Grün": "#8fd4ac"}
URTEIL = {"bestanden": "#4ea373", "durchgefallen": "#e2776f", "entwurf": "#6fb3d2"}
MARKE = "#ffc21a"   # Nummern im Schema — Farbe der Tafel, nicht der App
RAHMEN = "#2a2f38"  # das Gehäuse des iPad


# ── SVG-Bausteine ───────────────────────────────────────────────────────────────────────────────────

def _e(text: str) -> str:
    return html.escape(text, quote=True)


class Svg:
    """Ein kleines Zeichenblatt: Koordinaten in Punkten des iPad-Bildschirms (oder eines Ausschnitts)."""

    def __init__(self, b: int, h: int):
        self.b, self.h, self.t = b, h, []

    def rect(self, x, y, w, h, fill="none", stroke=None, rx=0, sw=1.5, dash=None, op=None):
        s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' opacity="{op}"' if op is not None else ""
        self.t.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"{s}{d}{o}/>')

    def line(self, x1, y1, x2, y2, stroke=LEISE, sw=1.5, dash=None, cap="round"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.t.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
                      f'stroke-width="{sw}" stroke-linecap="{cap}"{d}/>')

    def path(self, d, stroke=LEISE, sw=2, fill="none"):
        self.t.append(f'<path d="{d}" stroke="{stroke}" stroke-width="{sw}" fill="{fill}" '
                      'stroke-linecap="round" stroke-linejoin="round"/>')

    def circle(self, x, y, r, fill="none", stroke=None, sw=2, dash=None):
        s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.t.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"{s}{d}/>')

    def text(self, x, y, s, size=16, fill=SCHRIFT, weight=400, anchor="start", mono=False, spacing=None):
        fam = "PlexMono, monospace" if mono else "Plex, sans-serif"
        ls = f' letter-spacing="{spacing}"' if spacing else ""
        self.t.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
                      f'text-anchor="{anchor}" font-family="{fam}"{ls}>{_e(s)}</text>')

    def titel(self, x, y, s, size=13):
        """Abschnittstitel der App: klein, gesperrt, Grossbuchstaben."""
        self.text(x, y, s.upper(), size=size, fill=LEISE, weight=600, spacing="1.2")

    def knopf(self, x, y, w, h, label, gewaehlt=False, size=16, weight=500, aus=False):
        """`Wahlknopfstil`: gewählt grün umrandet auf grünlichem Grund, sonst Feld mit Linie."""
        self.rect(x, y, w, h, fill=GEW_GRUND if gewaehlt else FELD,
                  stroke=GEW_RAND if gewaehlt else LINIE, rx=10, sw=2 if gewaehlt else 1.5)
        self.text(x + w / 2, y + h / 2 + size * 0.36, label, size=size, weight=weight,
                  fill=LEISE if aus else SCHRIFT, anchor="middle")

    def marke(self, x, y, n, g=1.0):
        """Die Nummer der Tafel, die auf eine Zeile rechts verweist."""
        self.circle(x, y, 15 * g, fill=MARKE, stroke="#12151c", sw=3 * g)
        self.text(x, y + 6 * g, str(n), size=17 * g, fill="#12151c", weight=700, anchor="middle")

    def symbol(self, art, x, y, farbe=SCHRIFT, g=1.0):
        """Einfache Zeichen für die SF-Symbole der App — nur die Form, kein Nachbau."""
        def p(d):
            self.path(d, stroke=farbe, sw=2.2 * g)
        if art == "stift":
            p(f"M{x-10*g},{y+10*g} L{x+7*g},{y-7*g} L{x+10*g},{y-10*g} M{x-10*g},{y+10*g} l3,-8 l5,5 z")
        elif art == "radierer_strich":
            self.rect(x - 9 * g, y - 12 * g, 14 * g, 18 * g, stroke=farbe, sw=2 * g, rx=3)
            self.line(x - 12 * g, y + 12 * g, x + 12 * g, y + 12 * g, stroke=farbe, sw=2 * g, dash="3 3")
        elif art == "radierer":
            self.rect(x - 8 * g, y - 12 * g, 16 * g, 22 * g, stroke=farbe, sw=2 * g, rx=3)
            self.line(x - 8 * g, y + 2 * g, x + 8 * g, y + 2 * g, stroke=farbe, sw=2 * g)
        elif art == "hand":
            self.rect(x - 9 * g, y - 2 * g, 18 * g, 14 * g, stroke=farbe, sw=2 * g, rx=5)
            for dx in (-6, -2, 2, 6):
                self.line(x + dx * g, y - 2 * g, x + dx * g, y - 12 * g, stroke=farbe, sw=2 * g)
        elif art == "tauschen":
            p(f"M{x-12*g},{y-4*g} H{x+12*g} l-5,-5 M{x+12*g},{y+5*g} H{x-12*g} l5,5")
        elif art == "vollbild":
            p(f"M{x-11*g},{y-3*g} V{y-11*g} H{x-3*g} M{x-11*g},{y-11*g} l7,7 "
              f"M{x+11*g},{y+3*g} V{y+11*g} H{x+3*g} M{x+11*g},{y+11*g} l-7,-7")
        elif art == "zurueck":
            p(f"M{x+10*g},{y+8*g} V{y-1*g} a6,6 0 0 0 -6,-6 H{x-10*g} l6,-6 M{x-10*g},{y-7*g} l6,6")
        elif art == "vor":
            p(f"M{x-10*g},{y+8*g} V{y-1*g} a6,6 0 0 1 6,-6 H{x+10*g} l-6,-6 M{x+10*g},{y-7*g} l-6,6")
        elif art == "plus":
            p(f"M{x-9*g},{y} H{x+9*g} M{x},{y-9*g} V{y+9*g}")
        elif art == "kreuz":
            p(f"M{x-7*g},{y-7*g} L{x+7*g},{y+7*g} M{x+7*g},{y-7*g} L{x-7*g},{y+7*g}")
        elif art == "neu_laden":
            self.path(f"M{x+9*g},{y-2*g} a9,9 0 1 1 -3,-7", stroke=farbe, sw=2 * g)
            p(f"M{x+7*g},{y-14*g} l0,6 l-6,0")
        elif art == "schloss":
            self.rect(x - 6 * g, y - 1 * g, 12 * g, 10 * g, fill=farbe, rx=2)
            self.path(f"M{x-4*g},{y-1*g} v-4 a4,4 0 0 1 8,0 v4", stroke=farbe, sw=2 * g)
        elif art == "kasten_an":
            self.rect(x - 10 * g, y - 10 * g, 20 * g, 20 * g, fill=GEW_RAND, rx=4)
            p(f"M{x-5*g},{y} l4,4 l7,-8")
        elif art == "kasten_aus":
            self.rect(x - 10 * g, y - 10 * g, 20 * g, 20 * g, stroke=LEISE, sw=2 * g, rx=4)
        elif art == "hoch":
            p(f"M{x-7*g},{y+4*g} L{x},{y-4*g} L{x+7*g},{y+4*g}")
        elif art == "runter":
            p(f"M{x-7*g},{y-4*g} L{x},{y+4*g} L{x+7*g},{y-4*g}")
        elif art == "umbenennen":
            p(f"M{x-8*g},{y+9*g} H{x+8*g} M{x},{y-10*g} V{y+5*g} M{x-4*g},{y-10*g} H{x+4*g}")
        elif art == "papierkorb":
            self.rect(x - 7 * g, y - 6 * g, 14 * g, 16 * g, stroke=farbe, sw=2 * g, rx=2)
            p(f"M{x-10*g},{y-6*g} H{x+10*g} M{x-3*g},{y-10*g} H{x+3*g}")
        elif art == "bleistift":
            p(f"M{x-8*g},{y+8*g} L{x+6*g},{y-6*g} l3,3 L{x-5*g},{y+11*g} z")
        elif art == "teilen":
            self.rect(x - 9 * g, y - 3 * g, 18 * g, 15 * g, stroke=farbe, sw=2 * g, rx=2)
            p(f"M{x},{y+5*g} V{y-13*g} M{x-5*g},{y-8*g} L{x},{y-13*g} L{x+5*g},{y-8*g}")
        elif art == "links":
            p(f"M{x+4*g},{y-9*g} L{x-5*g},{y} L{x+4*g},{y+9*g}")
        elif art == "bild":
            self.rect(x - 10 * g, y - 8 * g, 20 * g, 16 * g, stroke=farbe, sw=2 * g, rx=2)
            p(f"M{x-8*g},{y+6*g} l6,-6 l4,4 l3,-3 l5,5")
        elif art == "uhr":
            self.circle(x, y, 10 * g, stroke=farbe, sw=2 * g)
            p(f"M{x},{y-6*g} V{y} l4,3")
        elif art == "pfeil_runter":
            self.circle(x, y, 10 * g, stroke=farbe, sw=2 * g)
            p(f"M{x},{y-5*g} V{y+5*g} M{x-4*g},{y+1*g} L{x},{y+5*g} L{x+4*g},{y+1*g}")

    def statuspunkt(self, x, y, zustand):
        """`Statuspunkt`: grün gefüllt nur gekoppelt, grau bei Suche (atmet), hohl bei aus und getrennt."""
        if zustand == "gekoppelt":
            self.circle(x, y, 7, fill=GEW_RAND)
        elif zustand == "suche":
            self.circle(x, y, 7, fill=LEISE)
            self.circle(x, y, 12, stroke=LEISE, sw=1, dash="2 3")
        else:
            self.circle(x, y, 6, stroke=LEISE, sw=2)

    def ipad(self, x, y, w, h):
        """Das Gehäuse um einen Bildschirm."""
        self.rect(x - 22, y - 22, w + 44, h + 44, fill=RAHMEN, rx=34)
        self.rect(x, y, w, h, fill=GRUND, rx=10)

    def svg(self, breite: int | str = "100%") -> str:
        return (f'<svg width="{breite}" viewBox="0 0 {self.b} {self.h}" xmlns="http://www.w3.org/2000/svg">'
                + "".join(self.t) + "</svg>")


def _skizze_haus(s: Svg, x, y, w, h, farbe=STIFT["Orange"], sw=3.0):
    """Eine erfundene, synthetische Strichskizze (Regel 3): ein Haus mit Satteldach."""
    bx, by, bw, bh = x + w * 0.28, y + h * 0.42, w * 0.44, h * 0.4
    s.path(f"M{bx},{by+bh} V{by} L{bx+bw/2},{by-h*0.2} L{bx+bw},{by} V{by+bh} Z", stroke=farbe, sw=sw)
    s.path(f"M{bx+bw*0.18},{by+bh} v-{bh*0.45} h{bw*0.16} v{bh*0.45}", stroke=farbe, sw=sw * 0.8)
    s.rect(bx + bw * 0.55, by + bh * 0.2, bw * 0.25, bh * 0.25, stroke=farbe, sw=sw * 0.8)
    s.line(x + w * 0.08, by + bh, x + w * 0.92, by + bh, stroke=farbe, sw=sw * 0.7)


# ── die Schemata ────────────────────────────────────────────────────────────────────────────────────
# Masse in Punkten wie in der App: Leiste 88 breit, Seitenfeld 340, Verbindungszeile ≥ 72, Ziele 60 × 60.

def _werkzeugleiste(s: Svg, x, y, h, nummern=False):
    s.rect(x, y, 88, h, fill=LEISTE)
    yy = y + 16
    for i, art in enumerate(("stift", "radierer_strich", "radierer", "hand")):
        s.rect(x + 14, yy, 60, 60, fill=GEW_GRUND if i == 0 else FELD,
               stroke=GEW_RAND if i == 0 else LINIE, rx=10, sw=2 if i == 0 else 1.5)
        s.symbol(art, x + 44, yy + 30)
        yy += 70
    s.line(x + 22, yy + 2, x + 66, yy + 2, stroke=LINIE)
    yy += 12
    for i, dicke in enumerate((2, 4.5, 8)):
        s.rect(x + 14, yy, 60, 60, fill=GEW_GRUND if i == 1 else FELD,
               stroke=GEW_RAND if i == 1 else LINIE, rx=10, sw=2 if i == 1 else 1.5)
        s.line(x + 33, yy + 40, x + 55, yy + 20, stroke=SCHRIFT, sw=dicke)
        yy += 70
    s.line(x + 22, yy + 2, x + 66, yy + 2, stroke=LINIE)
    yy += 12
    marken = {}
    for art in ("tauschen", "vollbild"):
        if yy + 60 > y + h:
            break
        s.rect(x + 14, yy, 60, 60, fill=FELD, stroke=LINIE, rx=10)
        s.symbol(art, x + 44, yy + 30)
        marken[art] = yy + 30
        yy += 70
    return marken


def _verbindungszeile(s: Svg, x, y, w, zustand="gekoppelt", wort="Gekoppelt",
                      detail="Mac · über den Mac, verschlüsselt · antwortet", fach="Parkfach",
                      schloss=True, strecke=None):
    s.rect(x, y, w, 72, fill=LEISTE)
    s.statuspunkt(x + 26, y + 36, zustand)
    tx = x + 46
    if schloss:
        s.symbol("schloss", tx + 6, y + 27, g=0.9)
        tx += 20
    s.text(tx, y + 32, wort, size=17, weight=600)
    s.text(x + 46, y + 55, detail, size=13, fill=LEISE)
    if strecke:
        _uebergabe(s, x + w - 230 - (150 if fach else 0), y + 14, 220, strecke)
    if fach:
        bw = max(110, 11 * len(fach) + 30)
        s.knopf(x + w - bw - 14, y + 12, bw, 48, fach, size=15)
    s.line(x, y + 72, x + w, y + 72, stroke=LINIE, sw=1)


def _uebergabe(s: Svg, x, y, w, phase):
    """`Uebergabestrecke`: ein Faden vom iPad zum Ziel, **eine** Marke darauf, darunter der Satz."""
    ort = {"ablegen": 0.04, "flug": 0.55, "warten": 0.9, "eingerastet": 1.0, "zurueck": 0.0}[phase[0]]
    s.text(x, y + 14, "iPad", size=11, fill=LEISE)
    s.text(x + w, y + 14, "Mac", size=11, fill=LEISE, anchor="end")
    s.line(x + 30, y + 10, x + w - 32, y + 10, stroke=LINIE, sw=2)
    if phase[0] == "flug":
        s.line(x + 30, y + 10, x + 30 + (w - 62) * ort, y + 10, stroke=GEW_RAND, sw=2)
    mx = x + 30 + (w - 62) * ort
    s.rect(mx - 7, y + 3, 14, 14, fill=SCHRIFT if phase[0] != "zurueck" else LEISE, rx=3)
    s.text(x + w / 2, y + 38, phase[1], size=11.5, fill=LEISE, anchor="middle")


def bild_uebersicht() -> str:
    s = Svg(1240, 880)
    X, Y, W, H = 23, 23, 1194, 834
    s.ipad(X, Y, W, H)
    _verbindungszeile(s, X, Y, W, fach="Parkfach")
    _werkzeugleiste(s, X, Y + 73, H - 73)
    # Seitenfeld (340)
    sx = X + W - 340
    s.rect(sx, Y + 73, 340, H - 73, fill=LEISTE)
    s.line(sx, Y + 73, sx, Y + H, stroke=LINIE, sw=1)
    s.titel(sx + 20, Y + 108, "Was die Skizze tut")
    s.knopf(sx + 20, Y + 120, 140, 44, "Prüfen", gewaehlt=True)
    s.knopf(sx + 170, Y + 120, 140, 44, "Entwerfen")
    s.knopf(sx + 20, Y + 190, 140, 44, "Ebenen", gewaehlt=True)
    s.knopf(sx + 170, Y + 190, 140, 44, "Mappe")
    s.titel(sx + 20, Y + 272, "Ebenen")
    s.rect(sx + 266, Y + 250, 44, 44, fill=FELD, stroke=LINIE, rx=10)
    s.symbol("plus", sx + 288, Y + 272)
    for i, (name, wert, aktiv) in enumerate((("Variante B", "leer", False), ("Variante A", "100 %", True))):
        yy = Y + 306 + i * 54
        s.rect(sx + 20, yy, 300, 46, fill=GEW_GRUND if aktiv else "none",
               stroke=GEW_RAND if aktiv else LINIE, rx=10, sw=1)
        s.symbol("kasten_an", sx + 44, yy + 23)
        s.text(sx + 70, yy + 29, name, size=15, weight=600 if aktiv else 400)
        s.text(sx + 306, yy + 29, wert, size=13, fill=LEISE, anchor="end", mono=True)
    s.text(sx + 20, Y + 440, "Geht mit: 1 von 2 Ebenen.", size=14, weight=600)
    s.rect(sx, Y + H - 96, 340, 96, fill=LEISTE)
    s.line(sx, Y + H - 96, sx + 340, Y + H - 96, stroke=LINIE, sw=1)
    s.knopf(sx + 20, Y + H - 76, 300, 56, "In die Mappe legen", gewaehlt=True, size=17, weight=600)
    # Bühne
    bx, bw = X + 88, W - 88 - 340
    s.rect(bx, Y + 73, bw, H - 73, fill=BUEHNE)
    s.text(bx + 20, Y + 112, "SKIZZE · VARIANTE A", size=13, fill=LEISE, weight=600, spacing="1.2")
    s.text(bx + bw - 20, Y + 112, "1536 × 1024 px", size=13, fill=LEISE, anchor="end", mono=True)
    pw = bw - 40
    ph = pw * 1024 / 1536
    s.rect(bx + 20, Y + 126, pw, ph, fill=PAPIER, stroke=LINIE)
    _skizze_haus(s, bx + 20, Y + 126, pw, ph)
    ty = Y + 126 + ph + 18
    for i, art in enumerate(("zurueck", "vor")):
        s.rect(bx + 20 + i * 70, ty, 60, 60, fill=FELD, stroke=LINIE, rx=10)
        s.symbol(art, bx + 50 + i * 70, ty + 30)
    s.text(bx + 74, ty + 55, "12", size=10, fill=LEISE, anchor="end", mono=True)
    for i, farbe in enumerate(STIFT.values()):
        s.circle(bx + bw - 236 + i * 52, ty + 30, 17, fill=farbe, stroke=SCHRIFT if i == 0 else LINIE, sw=2)
    s.circle(bx + bw - 236 + 4 * 52, ty + 30, 17, fill="url(#regenbogen)", stroke=LINIE, sw=2)
    s.t.insert(0, '<defs><linearGradient id="regenbogen"><stop offset="0" stop-color="#e2776f"/>'
                  '<stop offset=".5" stop-color="#8fd4ac"/><stop offset="1" stop-color="#6fb3d2"/>'
                  '</linearGradient></defs>')
    s.marke(X + 340, Y + 36, 1, g=1.6)
    s.marke(X + 88, Y + 120, 2, g=1.6)
    s.marke(bx + bw / 2, Y + 126 + ph / 2 - 120, 3, g=1.6)
    s.marke(sx + 326, Y + 100, 4, g=1.6)
    s.marke(sx + 326, Y + H - 48, 5, g=1.6)
    return s.svg()


def bild_zusammenspiel() -> str:
    """iPad → Mac → Heim-PC, wie es die Verbindung heute macht (Entscheid 118, Kern/Macmappensicht.swift)."""
    s = Svg(680, 250)
    kasten = [(10, "iPad", "draws, sends, shows"), (250, "Mac", "keeps the project folder"),
              (490, "Home PC", "computes the images")]
    for x, t, u in kasten:
        s.rect(x, 40, 180, 110, fill=FELD, stroke=LINIE, rx=14)
        s.text(x + 90, 88, t, size=24, weight=600, anchor="middle")
        s.text(x + 90, 118, u, size=15, fill=LEISE, anchor="middle")
    s.path("M196,95 H244 l-8,-7 M244,95 l-8,7", stroke=GEW_RAND, sw=3)
    s.symbol("schloss", 220, 70, farbe=GEW_RAND)
    s.text(220, 178, "encrypted, paired", size=13, fill=LEISE, anchor="middle")
    s.path("M436,95 H484 l-8,-7 M484,95 l-8,7", stroke=LEISE, sw=3)
    s.text(460, 178, "jobs and results", size=13, fill=LEISE, anchor="middle")
    s.text(340, 232, "The iPad never computes itself.", size=15, fill=SCHRIFT, anchor="middle", weight=600)
    return s.svg()


def bild_koppeln() -> str:
    s = Svg(700, 1120)
    s.rect(10, 10, 680, 1100, fill=GRUND, stroke=LINIE, rx=18)
    s.rect(10, 10, 680, 60, fill=LEISTE, rx=18)
    s.rect(10, 50, 680, 20, fill=LEISTE)
    s.text(350, 48, "Mit dem Mac koppeln", size=18, weight=600, anchor="middle")
    s.text(664, 48, "Fertig", size=17, weight=600, fill=GEW_RAND, anchor="end")
    x = 44
    s.titel(x, 106, "Mac in der Nähe")
    s.rect(x, 118, 612, 196, fill=FELD, stroke=LINIE, rx=12)
    s.text(x + 18, 152, "Mit diesem Mac koppeln?", size=18, weight=600)
    s.text(x + 18, 182, "Mac", size=18, mono=True)
    s.text(x + 18, 212, "Danach fragt der Mac noch einmal. Erst wenn beide zustimmen,", size=13, fill=LEISE)
    s.text(x + 18, 230, "schickt er Adresse und Zahl — nie das Kennwort.", size=13, fill=LEISE)
    s.knopf(x + 18, 248, 160, 50, "Ablehnen")
    s.knopf(x + 190, 248, 160, 50, "Annehmen", gewaehlt=True)
    s.titel(x, 350, "Oder den QR-Code lesen")
    s.knopf(x, 362, 260, 54, "Mit QR-Code koppeln")
    s.text(x, 440, "Der Mac zeigt ihn unter «iPad koppeln», zwei Minuten lang.", size=13, fill=LEISE)
    s.titel(x, 482, "Macs im WLAN")
    s.rect(x, 494, 612, 56, fill=GEW_GRUND, stroke=GEW_RAND, rx=10, sw=2)
    s.symbol("schloss", x + 22, 518)
    s.text(x + 40, 528, "Mac", size=16)
    s.text(x + 596, 528, "https://…", size=13, fill=LEISE, anchor="end", mono=True)
    s.titel(x, 590, "Oder die Adresse des Mac eintippen")
    s.rect(x, 602, 612, 58, fill=FELD, stroke=LINIE, rx=10)
    s.text(x + 16, 639, "https://…", size=18, fill=LEISE, mono=True)
    s.text(x, 684, "Immer https — unverschlüsselt koppelt das iPad nicht.", size=13, fill=LEISE)
    s.titel(x, 726, "Zahl eintippen — vom Mac")
    s.rect(x, 738, 612, 78, fill=FELD, stroke=LINIE, rx=12)
    s.text(350, 793, "000000", size=40, fill=LEISE, anchor="middle", mono=True)
    s.text(x, 840, "Gilt nur für wenige Versuche.", size=13, fill=LEISE)
    s.knopf(x, 866, 200, 58, "Koppeln", aus=True)
    s.line(x, 950, x + 612, 950, stroke=LINIE, dash="4 4")
    s.text(x + 612, 972, "once paired, at the end:", size=12, fill=LEISE, anchor="end")
    s.titel(x, 994, "Gekoppelt")
    s.symbol("schloss", x + 8, 1018)
    s.text(x + 24, 1026, "Über den Mac, verschlüsselt · Zeichen des Mac: …", size=14)
    s.knopf(x, 1044, 150, 54, "Trennen")
    s.marke(668, 106, 1)
    s.marke(668, 389, 2)
    s.marke(668, 482, 3)
    s.marke(668, 631, 4)
    s.marke(668, 777, 5)
    s.marke(262, 895, 6)
    return s.svg()


def bild_verbindung() -> str:
    s = Svg(700, 560)
    zeilen = [
        ("aus", "Aus", "Nicht gekoppelt. Skizzen warten auf dem iPad.", None, False),
        ("suche", "Suche", "Mac · über den Mac, verschlüsselt hat noch nicht geantwortet …", None, False),
        ("gekoppelt", "Gekoppelt", "Mac · über den Mac, verschlüsselt · antwortet", "2 geparkt", True),
        ("getrennt", "Getrennt", "(der Grund, warum die letzte Anfrage nicht ankam)", "1 ungewiss", False),
    ]
    for i, (z, wort, detail, fach, schloss) in enumerate(zeilen):
        y = 10 + i * 96
        _verbindungszeile(s, 10, y, 680, zustand=z, wort=wort, detail=detail, fach=fach, schloss=schloss)
        s.marke(690 - 12, y + 6, i + 1)
    y = 10 + 4 * 96 + 24
    _verbindungszeile(s, 10, y, 680, wort="Gekoppelt", fach=None,
                      detail="Mac · über den Mac, verschlüsselt · antwortet",
                      strecke=("flug", "2.1 von 3.8 MB · gezählt"))
    s.marke(678, y + 6, 6)
    s.marke(560, 10 + 2 * 96 + 6, 5)
    return s.svg()


def bild_zeichnen() -> str:
    s = Svg(720, 770)
    _werkzeugleiste(s, 10, 10, 750)
    bx = 98
    s.rect(bx, 10, 612, 750, fill=BUEHNE)
    s.text(bx + 16, 46, "SKIZZE · VARIANTE A", size=13, fill=LEISE, weight=600, spacing="1.2")
    s.text(bx + 596, 46, "1536 × 1024 px", size=13, fill=LEISE, anchor="end", mono=True)
    pw, ph = 580, 580 * 1024 / 1536
    s.rect(bx + 16, 60, pw, ph, fill=PAPIER, stroke=LINIE)
    _skizze_haus(s, bx + 16, 60, pw, ph)
    s.path(f"M{bx+90},{60+ph-40} q60,-30 120,0 t120,0", stroke=STIFT["Blau"], sw=4)
    ty = 60 + ph + 20
    for i, art in enumerate(("zurueck", "vor")):
        s.rect(bx + 16 + i * 70, ty, 60, 60, fill=FELD, stroke=LINIE, rx=10)
        s.symbol(art, bx + 46 + i * 70, ty + 30)
    s.text(bx + 70, ty + 55, "12", size=10, fill=LEISE, anchor="end", mono=True)
    for i, farbe in enumerate(STIFT.values()):
        s.circle(bx + 340 + i * 48, ty + 30, 16, fill=farbe, stroke=SCHRIFT if i == 0 else LINIE, sw=2)
    s.circle(bx + 340 + 4 * 48, ty + 30, 16, fill=FELD, stroke=LEISE, sw=2, dash="3 3")
    s.text(bx + 340 + 4 * 48, ty + 35, "+", size=16, fill=LEISE, anchor="middle")
    # ausgeblendete Ebene: der Hinweis, wie er erscheint
    hy = ty + 96
    s.rect(bx + 70, hy, 470, 150, fill=FELD, rx=12)
    s.text(bx + 305, hy + 38, "«Variante B» ist ausgeblendet.", size=16, weight=600, anchor="middle")
    s.text(bx + 305, hy + 64, "Auf eine ausgeblendete Ebene wird nicht gezeichnet.", size=13,
           fill=LEISE, anchor="middle")
    s.knopf(bx + 225, hy + 84, 160, 44, "Einblenden", gewaehlt=True)
    s.text(bx + 305, hy + 178, "(appears over the sheet only when the chosen layer is hidden)", size=12,
           fill=LEISE, anchor="middle")
    for i, y in enumerate((56, 126, 196, 266)):
        s.marke(98, y, i + 1)
    s.marke(98, 366, 5)
    s.marke(98, 586, 6)
    s.marke(98, 656, 7)
    s.marke(bx + 150, ty + 8, 8)
    s.marke(bx + 340 + 4 * 48 + 30, ty + 8, 9)
    return s.svg()


def bild_ebenen() -> str:
    s = Svg(380, 530)
    s.rect(0, 0, 380, 530, fill=LEISTE)
    x = 20
    s.titel(x, 40, "Ebenen")
    s.rect(316, 16, 44, 44, fill=FELD, stroke=LINIE, rx=10)
    s.symbol("plus", 338, 38)
    reihen = [("Variante C", "ausgeblendet", False, False), ("Variante B", "leer", True, False),
              ("Variante A", "80 %", True, True)]
    for i, (name, wert, sichtbar, aktiv) in enumerate(reihen):
        y = 74 + i * 56
        s.rect(x, y, 340, 48, fill=GEW_GRUND if aktiv else "none", stroke=GEW_RAND if aktiv else LINIE,
               rx=10, sw=1)
        s.symbol("kasten_an" if sichtbar else "kasten_aus", x + 24, y + 24)
        s.text(x + 50, y + 30, name, size=15, weight=600 if aktiv else 400, fill=SCHRIFT if sichtbar else LEISE)
        s.text(x + 326, y + 30, wert, size=13, fill=LEISE, anchor="end", mono=True)
    y = 74 + 3 * 56
    s.rect(x, y, 340, 48, stroke=LINIE, rx=10, sw=1, dash="4 3")
    s.symbol("kasten_an", x + 24, y + 24)
    s.symbol("bild", x + 58, y + 24, farbe=LEISE, g=0.8)
    s.text(x + 76, y + 30, "Bild 07", size=15)
    s.text(x + 268, y + 30, "Unterlage", size=13, fill=LEISE, anchor="end", mono=True)
    s.rect(x + 284, y + 4, 44, 40, fill=FELD, stroke=LINIE, rx=10)
    s.symbol("kreuz", x + 306, y + 24)
    y += 74
    s.text(x, y, "Deckkraft", size=13, fill=LEISE)
    s.text(x + 340, y, "80 %", size=13, fill=LEISE, anchor="end", mono=True)
    s.line(x, y + 22, x + 340, y + 22, stroke=LINIE, sw=4)
    s.line(x, y + 22, x + 262, y + 22, stroke=GEW_RAND, sw=4)
    s.circle(x + 262, y + 22, 11, fill=SCHRIFT)
    y += 46
    for i, art in enumerate(("hoch", "runter", "umbenennen", "papierkorb")):
        s.rect(x + i * 54, y, 44, 44, fill=FELD, stroke=LINIE, rx=10)
        s.symbol(art, x + 22 + i * 54, y + 22)
    y += 80
    s.text(x, y, "Geht mit: 1 von 3 Ebenen.", size=14, weight=600)
    s.text(x, y + 30, "Jede Ebene ist eine Variante. Gerechnet wird,", size=12.5, fill=LEISE)
    s.text(x, y + 48, "was sichtbar ist — unsichtbare Ebenen gehen nicht mit.", size=12.5, fill=LEISE)
    s.marke(300, 38, 1)
    s.marke(x + 190, 74 + 24, 2)
    s.marke(250, 74 + 2 * 56 + 2, 3)
    s.marke(360, 74 + 3 * 56 + 92, 4)
    s.marke(x + 210, 74 + 3 * 56 + 142, 5)
    s.marke(360, 74 + 3 * 56 + 2, 6)
    s.marke(360, 74 + 3 * 56 + 194, 7)
    return s.svg()


def bild_senden() -> str:
    s = Svg(700, 720)
    phasen = [("ablegen", "legt ab …"), ("flug", "2.1 von 3.8 MB · gezählt"),
              ("warten", "alles drüben · wartet auf die Bestätigung"),
              ("eingerastet", "in der Mappe · noch nicht gerechnet"),
              ("zurueck", "nicht angekommen · liegt auf dem iPad, siehe Parkfach")]
    s.titel(10, 22, "In the status line, while a sketch travels")
    for i, ph in enumerate(phasen):
        y = 40 + i * 64
        s.rect(10, y, 680, 56, fill=LEISTE, rx=10)
        _uebergabe(s, 150, y + 6, 400, ph)
    s.marke(678, 46, 2)
    y0 = 40 + 5 * 64 + 26
    s.titel(10, y0, "Foot of the side panel")
    s.rect(10, y0 + 12, 680, 300, fill=LEISTE, rx=12)
    s.line(10, y0 + 12, 690, y0 + 12, stroke=LINIE)
    s.knopf(36, y0 + 34, 360, 56, "In die Mappe legen", gewaehlt=True, size=17, weight=600)
    s.text(36, y0 + 126, "(the sentence, when there is one — e.g. nothing drawn, or parked", size=13, fill=SCHRIFT)
    s.text(36, y0 + 146, "because nobody answers)", size=13, fill=SCHRIFT)
    for i, z in enumerate(("Sie wird als offen abgelegt und wartet — gerechnet wird erst auf",
                           "«Rechnen lassen» in der Mappe. …")):
        s.text(36, y0 + 186 + i * 20, z, size=13, fill=LEISE)
    s.text(36, y0 + 270, "Under both tabs, fixed at the foot — the content scrolls above it.", size=13,
           fill=LEISE)
    s.marke(410, y0 + 40, 1)
    s.marke(560, y0 + 136, 3)
    return s.svg()


def bild_parkfach() -> str:
    s = Svg(700, 800)
    s.rect(10, 10, 680, 780, fill=GRUND, stroke=LINIE, rx=18)
    s.rect(10, 10, 680, 60, fill=LEISTE, rx=18)
    s.rect(10, 50, 680, 20, fill=LEISTE)
    s.text(350, 48, "Parkfach", size=18, weight=600, anchor="middle")
    s.text(664, 48, "Fertig", size=17, weight=600, fill=GEW_RAND, anchor="end")
    reihen = [
        ("GEPARKT", "Wartet. Zuletzt: (Grund)", [], True),
        ("UNTERWEGS", "Wird gerade gesendet.", None, True),
        ("ANGEKOMMEN", "Drüben abgelegt.", ["Verwerfen"], False),
        ("ABGEWIESEN", "Abgewiesen: (Satz des Servers)", ["Noch einmal senden", "Verwerfen"], True),
        ("UNGEWISS", "(Grund) Sie geht mit demselben Schlüssel von selbst noch einmal …", ["Verwerfen"], True),
    ]
    for i, (wort, satz, knoepfe, zeichnung) in enumerate(reihen):
        y = 92 + i * 136
        if zeichnung:
            s.rect(36, y, 96, 64, fill="#ffffff", rx=6)
            _skizze_haus(s, 36, y, 96, 64, farbe="#444a55", sw=1.6)
        else:
            s.rect(36, y, 96, 64, stroke=LINIE, rx=6)
            s.text(84, y + 37, "drüben", size=11, fill=LEISE, anchor="middle", mono=True)
        s.text(150, y + 16, wort, size=12.5, weight=600, spacing="0.9",
               fill=SCHRIFT if wort in ("GEPARKT", "UNTERWEGS") else LEISE)
        s.text(150 + 12 * len(wort) + 14, y + 16, "24.10.2026 · 14:05", size=12, fill=LEISE, mono=True)
        s.text(150, y + 42, satz, size=13, fill=LEISE)
        if knoepfe is None:
            continue
        knoepfe = knoepfe or ["Verwerfen"]
        bx = 150
        for k in knoepfe:
            w = 30 + 9.5 * len(k)
            s.knopf(bx, y + 58, w, 52, k, size=15)
            bx += w + 10
        s.marke(670, y + 12, i + 1)
    s.marke(670, 92 + 136 + 12, 2)
    s.marke(132, 92 + 3 * 136 + 84, 6)
    return s.svg()


def bild_mappe() -> str:
    s = Svg(380, 1000)
    s.rect(0, 0, 380, 1000, fill=LEISTE)
    x = 20
    s.text(x, 44, "Testhaus", size=22, weight=600)
    s.rect(316, 16, 44, 44, fill=FELD, stroke=LINIE, rx=10)
    s.symbol("neu_laden", 338, 40)
    s.titel(x, 98, "Was die Skizze tut")
    s.knopf(x, 110, 165, 44, "Prüfen", gewaehlt=True)
    s.knopf(x + 175, 110, 165, 44, "Entwerfen")
    s.titel(x, 196, "Lauf")
    s.text(x, 224, "(Schritt)", size=15, weight=600)
    s.text(x + 340, 224, "7 von 20", size=13, fill=LEISE, anchor="end", mono=True)
    s.line(x, 240, x + 340, 240, stroke=LINIE, sw=6)
    s.line(x, 240, x + 119, 240, stroke=GEW_RAND, sw=6)
    s.knopf(x, 258, 200, 44, "Lauf abbrechen")
    s.titel(x, 344, "Drei Varianten")
    s.knopf(x, 356, 165, 44, "Drei Startwerte", gewaehlt=True, size=14)
    s.knopf(x + 175, 356, 165, 44, "Drei Ebenen", size=14)
    s.knopf(x, 410, 340, 52, "Drei Startwerte rechnen", gewaehlt=True, size=15)
    s.titel(x, 504, "Bilder")
    for i, (farbe, wort, strich) in enumerate(((URTEIL["bestanden"], "BESTANDEN", None),
                                              (URTEIL["entwurf"], "ENTWURF", None),
                                              (LEISE, "NICHT GEMESSEN", "6 4"))):
        bx = x + i * 116
        s.rect(bx, 518, 104, 104, fill="#2a3038", stroke=farbe, sw=4, rx=4, dash=strich)
        s.rect(bx, 600, 104, 22, fill=farbe if not strich else FELD)
        s.text(bx + 52, 616, wort, size=9 if len(wort) > 10 else 10, weight=700, fill="#12151c" if not strich else LEISE,
               anchor="middle")
        _skizze_haus(s, bx, 512, 104, 90, farbe="#c9ccd2", sw=1.5)
    s.titel(x, 672, "Skizzen")
    s.text(x + 340, 672, "2 · 1 offen", size=12, fill=LEISE, anchor="end", mono=True)
    for i, (name, stand, erster) in enumerate((("(Skizze)", "offen", "Rechnen lassen"),
                                              ("(Skizze)", "gerechnet", "Bild ansehen"))):
        y = 690 + i * 150
        s.rect(x, y, 340, 136, fill=FELD, rx=10)
        s.text(x + 14, y + 28, name, size=15, weight=600)
        s.text(x + 326, y + 28, stand, size=12, fill=LEISE, anchor="end", mono=True)
        s.knopf(x + 14, y + 40, 170, 40, erster, gewaehlt=(i == 0), size=14)
        s.knopf(x + 14, y + 86, 170, 40, "Namen geben", size=14)
    s.marke(300, 40, 1)
    s.marke(360, 98, 2)
    s.marke(360, 196, 3)
    s.marke(360, 344, 4)
    s.marke(360, 504, 5)
    s.marke(250, 666, 6)
    return s.svg()


def bild_bildansicht() -> str:
    s = Svg(1240, 880)
    X, Y, W, H = 23, 23, 1194, 834
    s.ipad(X, Y, W, H)
    s.rect(X, Y, W, 76, fill=LEISTE)
    s.rect(X + 20, Y + 8, 60, 60, fill=FELD, stroke=LINIE, rx=10)
    s.symbol("links", X + 50, Y + 38)
    s.text(X + 100, Y + 48, "Bild 07", size=26)
    s.rect(X + 210, Y + 8, 60, 60, fill=FELD, stroke=LINIE, rx=10)
    s.symbol("bleistift", X + 240, Y + 38)
    s.rect(X + W - 150, Y + 12, 130, 52, fill=FELD, stroke=LINIE, rx=10)
    s.symbol("teilen", X + W - 124, Y + 40)
    s.text(X + W - 104, Y + 45, "Teilen", size=17)
    # Vorher / Nachher nebeneinander
    fx = X + W - 360
    bw = (fx - X - 60) / 2
    for i, (titel, rand) in enumerate((("Unterlage", None), ("Aus der KI", URTEIL["bestanden"]))):
        bx = X + 20 + i * (bw + 20)
        s.titel(bx, Y + 118, titel, size=14)
        s.rect(bx, Y + 130, bw, bw * 1024 / 1536, fill="#2a3038", stroke=rand or LINIE, sw=6 if rand else 1.5)
        _skizze_haus(s, bx, Y + 130, bw, bw * 1024 / 1536, farbe="#c9ccd2" if rand else "#8a919c", sw=2.4)
        if rand:
            s.rect(bx, Y + 130 + bw * 1024 / 1536 - 30, bw, 30, fill=rand)
            s.text(bx + 12, Y + 130 + bw * 1024 / 1536 - 9, "BESTANDEN  0.93", size=16, weight=700,
                   fill="#12151c")
    s.knopf(X + 20, Y + 400, 200, 44, "Nebeneinander", gewaehlt=True, size=15)
    s.knopf(X + 230, Y + 400, 200, 44, "Wischregler", size=15)
    s.text(X + 20, Y + 480, "Links die KI, rechts die Unterlage — with the slider («Schnitt»).", size=15,
           fill=LEISE)
    # Feld rechts (360)
    s.rect(fx, Y + 76, 360, H - 76, fill=LEISTE)
    s.line(fx, Y + 76, fx, Y + H, stroke=LINIE)
    s.titel(fx + 20, Y + 112, "Skizzieren", size=14)
    s.knopf(fx + 20, Y + 124, 320, 54, "Darauf skizzieren", gewaehlt=True, size=17)
    s.titel(fx + 20, Y + 222, "Wie das Bild gelesen wird", size=14)
    s.knopf(fx + 20, Y + 234, 155, 46, "Prüfen", gewaehlt=True)
    s.knopf(fx + 185, Y + 234, 155, 46, "Entwerfen")
    s.titel(fx + 20, Y + 326, "Was der Server sagt", size=14)
    s.text(fx + 20, Y + 360, "BESTANDEN · 0.93", size=19, weight=600, fill=URTEIL["bestanden"])
    s.text(fx + 20, Y + 388, "Schwelle 0.85", size=16, fill=LEISE, mono=True)
    s.titel(fx + 20, Y + 436, "Hinweise der Bildstufe", size=14)
    s.text(fx + 20, Y + 464, "Gemessen, ohne Hinweis.", size=16, fill=LEISE)
    s.knopf(fx + 20, Y + 500, 320, 54, "Varianten nebeneinander")
    s.titel(fx + 20, Y + 600, "Datei", size=14)
    s.text(fx + 20, Y + 628, "(file name)", size=15, fill=LEISE, mono=True)
    s.text(fx + 20, Y + 672, "Beim Teilen geht das Zeichen mit:", size=14, fill=LEISE)
    s.text(fx + 20, Y + 692, "Der Vorbehalt steht auf dem Bild.", size=14, fill=LEISE)
    s.marke(X + 290, Y + 38, 1, g=1.6)
    s.marke(X + 20 + bw + 20 + bw - 10, Y + 150, 2, g=1.6)
    s.marke(X + 450, Y + 422, 3, g=1.6)
    s.marke(fx + 340, Y + 112, 4, g=1.6)
    s.marke(fx + 340, Y + 222, 5, g=1.6)
    s.marke(fx + 340, Y + 326, 6, g=1.6)
    s.marke(fx + 340, Y + 527, 7, g=1.6)
    s.marke(X + W - 160, Y + 38, 8, g=1.6)
    return s.svg()


def bild_einstellungen() -> str:
    s = Svg(700, 470)
    _verbindungszeile(s, 10, 10, 680, fach=None)
    for i, (art, satz) in enumerate((("pfeil_runter", "Neue Fassung 0.x.y verfügbar — am Mac in Xcode aufspielen"),
                                     ("uhr", "Die App läuft in 2 Tagen ab — am Mac in Xcode neu aufspielen (▶)"))):
        y = 83 + i * 58
        s.rect(10, y, 680, 56, fill=FELD)
        s.symbol(art, 40, y + 28, farbe=SCHRIFT)
        s.text(66, y + 33, satz, size=14)
        s.symbol("kreuz", 664, y + 28, farbe=LEISE, g=0.8)
        s.marke(630, y + 4, i + 1)
    s.line(10, 199, 690, 199, stroke=LINIE)
    s.titel(10, 250, "Remembered on this iPad — no settings page")
    for i, satz in enumerate(("Toolbar side: left or right (Leiste auf die andere Seite)",
                              "The paired Mac: address, and its key in the iPad keychain",
                              "The project folder field from the pairing screen",
                              "Not remembered: tool and stroke — every start with the pen")):
        y = 282 + i * 44
        s.rect(10, y - 24, 680, 38, fill=FELD if i < 3 else "none", stroke=None if i < 3 else LINIE,
               rx=8, dash=None if i < 3 else "4 3")
        s.text(26, y + 1, satz, size=15, fill=SCHRIFT if i < 3 else LEISE)
    s.marke(678, 282 - 22, 3)
    s.marke(678, 282 + 3 * 44 - 22, 4)
    return s.svg()


def bild_grenzen() -> str:
    s = Svg(700, 690)
    s.titel(10, 24, "Built today", size=15)
    gebaut = ["Pencil draws, finger pans and zooms", "Layers, underlay, undo 20 steps",
              "Pair with the Mac: nearby, QR code, typed", "Parking bay — nothing gets lost",
              "Folder tab and image view with check mark"]
    for i, t in enumerate(gebaut):
        y = 40 + i * 58
        s.rect(10, y, 680, 48, fill=FELD, stroke=LINIE, rx=10)
        s.text(30, y + 31, t, size=17)
    y0 = 40 + 5 * 58 + 40
    s.rect(10, y0 - 20, 680, 690 - y0 + 10, stroke=MARKE, rx=14, dash="10 7", sw=2.5)
    s.text(30, y0 + 16, "PLANNED — DECIDED, NOT BUILT (AFTER THE DEMO)", size=15, weight=700, fill=MARKE,
           spacing="1.2")
    geplant = [("Finger drawing switch, default off", "141"),
               ("I8 · Sketch on a Visbox base, locked layer 60 %", "145"),
               ("I9 · Templates: plan, section, elevation, freehand", "145"),
               ("Floating islands, tool wheel top left", "135")]
    for i, (t, e) in enumerate(geplant):
        y = y0 + 40 + i * 64
        s.rect(30, y, 640, 52, stroke=LEISE, rx=10, dash="6 5", sw=1.5)
        s.text(50, y + 33, t, size=17, fill=LEISE)
        s.text(650, y + 33, "Decision " + e, size=13, fill=LEISE, anchor="end", mono=True)
    return s.svg()


# ── die Karten ──────────────────────────────────────────────────────────────────────────────────────
# `teile`: (Nummer im Schema oder None, englischer Begriff, Bildschirm-Beschriftung oder None, Satz). Die
# Beschriftung steht wortgleich im Swift-Code (Probe). `geplant`: (was, Entscheid) — nur dort steht Geplantes.

KARTEN: list[dict] = [
    {
        "kurz": "00-overview", "titel": "Overview: the iPad app at a glance",
        "hilfe": "A sketch pad for the Apple Pencil. Sketches go into the project folder (Mappe); finished "
                 "images come back to be looked at. The iPad itself never computes.",
        "bild": bild_uebersicht, "bild2": bild_zusammenspiel,
        "teile": [
            (1, "Status line", None, "Says whether the iPad is paired with the Mac and what is waiting to be "
                                     "sent. A tap opens pairing."),
            (2, "Toolbar", "Werkzeugleiste", "Pen, two erasers, the pan-and-zoom hand and three stroke widths — "
                                             "at the edge, never over the drawing."),
            (3, "Sheet", "Skizze · ", "The drawing sheet, always 1536 × 1024 pixels, drawn on with the Pencil."),
            (4, "Side panel", "Seitenfeld", "One column that switches between Layers (Ebenen) and Folder "
                                            "(Mappe) — never both at once."),
            (5, "Place in folder", "In die Mappe legen", "The one button that sends something out: the "
                                                         "visible layers as a sketch."),
        ],
        "geschieht": "Turning the iPad keeps the same view: in landscape the toolbar sits left or right, in "
                     "portrait at the bottom with the side panel below the sheet. Full screen (Vollbild) hides "
                     "everything but the sheet. The iPad talks only to the Mac, encrypted; with a project folder "
                     "open on the Mac, the sketch is kept there, otherwise the Mac passes it on to the home PC.",
        "grenze": "The app only shows what the computer says: verdicts, numbers and images come from there. "
                  "Without a paired Mac, sketches wait on the iPad.",
        "geplant": [],
        "quelle": "Startansicht.swift · Leiste/Arbeitsplatz.swift · Leiste/Seitentafel.swift · Kern/Macmappensicht.swift",
        "notiz": "What the iPad app is: a Pencil sketch pad that sends sketches into the project folder via the "
                 "Mac and shows the finished images — it never computes itself.",
    },
    {
        "kurz": "01-pairing", "titel": "Pairing with the Mac (Mit dem Mac koppeln)",
        "hilfe": "Connect the iPad to the Mac once. Three ways, from easiest to last resort — all three end in "
                 "the same pairing.",
        "bild": bild_koppeln,
        "teile": [
            (1, "Mac nearby", "Mac in der Nähe", "Appears when «iPad koppeln» is open on the Mac. The iPad asks "
                                                 "«Mit diesem Mac koppeln?» — Accept (Annehmen), then confirm on "
                                                 "the Mac. Only when both agree does the Mac send address and "
                                                 "number, never the password."),
            (2, "QR code", "Mit QR-Code koppeln", "Reads the code the Mac shows for two minutes, with the iPad "
                                                  "camera. Highlighted when no Mac shows up nearby."),
            (3, "Macs on the Wi-Fi", "Macs im WLAN", "Encrypted Macs found on the network. One: pre-selected. "
                                                     "Several: you choose — the app does not guess."),
            (4, "Type the address", "Oder die Adresse des Mac eintippen", "Always https; the app says what is "
                                                                          "wrong with an address before "
                                                                          "anything is sent."),
            (5, "Six-digit number", "Zahl eintippen — vom Mac", "Digits only, at most six, checked before "
                                                                "sending, so a typo costs no attempt. Cleared "
                                                                "after every try."),
            (6, "Pair", "Koppeln", "Active once address and number are complete; the answer appears below it."),
            (None, "Re-pair", "Neu koppeln", "If the paired Mac stops answering, nearby and QR code are offered "
                                             "again; the old pairing holds until the new one succeeds."),
            (None, "Disconnect", "Trennen", "Forgets the Mac on this iPad; parked sketches stay."),
        ],
        "geschieht": "After pairing the iPad accepts only this Mac's certificate. Under «Gekoppelt» it shows the "
                     "Mac's sign (Zeichen des Mac) to compare with the Mac's screen.",
        "grenze": "Only with the Mac and only encrypted — an old pairing straight to the home PC no longer "
                  "works. The nearby search needs «Lokales Netzwerk» allowed on the iPad; after 30 seconds "
                  "without a Mac the screen says so.",
        "geplant": [],
        "quelle": "Verbindung/Koppelbildschirm.swift · Naehesucher.swift · QRLeser.swift · Kern/Naehekopplung.swift",
        "notiz": "Three ways to pair the iPad with the Mac — nearby, QR code, or typing address and six-digit "
                 "number; re-pair without disconnecting; encrypted only.",
    },
    {
        "kurz": "02-status-line", "titel": "Status line (Verbindungszeile)",
        "hilfe": "The top line says who the iPad is talking to — and claims nothing it does not know.",
        "bild": bild_verbindung,
        "teile": [
            (1, "Off", "Aus", "Hollow ring. Not paired: «Nicht gekoppelt. Skizzen warten auf dem iPad.»"),
            (2, "Searching", "Suche", "Grey dot that breathes. Searching, or the paired Mac has not answered "
                                      "yet — «Gekoppelt» is shown only after an answer."),
            (3, "Paired", "Gekoppelt", "Green dot. The last request arrived; the lock means «über den Mac, "
                                       "verschlüsselt» (via the Mac, encrypted)."),
            (4, "Disconnected", "Getrennt", "Hollow ring. Paired, but the last request did not arrive — the "
                                            "reason is written underneath."),
            (5, "Parking bay button", "Parkfach", "Only counts that are not zero: parked (geparkt), uncertain "
                                                  "(ungewiss), on the way (unterwegs), open (offen). A tap opens "
                                                  "the list."),
            (6, "Hand-over strip", None, "While a sketch travels, one mark moves along a thread from iPad to "
                                         "Mac — see card 05."),
        ],
        "geschieht": "A tap on the status opens pairing. When the app comes back to the front, it asks the "
                     "remembered Mac again. With Reduce Motion on, the dot does not breathe.",
        "grenze": "The dot is never the whole message — the word next to it is. In full screen the line is "
                  "hidden, and with it the travelling mark.",
        "geplant": [],
        "quelle": "Verbindung/Verbindungszeile.swift · Uebergabe.swift · Kern/Suche.swift · Kern/Parkfach.swift",
        "notiz": "The four connection states Off, Searching, Paired, Disconnected, the parking bay button and "
                 "the hand-over strip in the iPad's top line.",
    },
    {
        "kurz": "03-drawing", "titel": "Drawing sheet (Zeichenfläche)",
        "hilfe": "Only the Pencil draws. Fingers move and zoom the sheet.",
        "bild": bild_zeichnen,
        "teile": [
            (1, "Pen", "Stift", "Pressure changes the line width; the width chosen below is the base."),
            (2, "Eraser: whole strokes", "Radierer: ganze Striche", "Removes a stroke with one touch."),
            (3, "Eraser: wipe area", "Radierer: flächig wegwischen", "Rubs away like a real eraser."),
            (4, "Pan and zoom", "Schieben und zoomen", "With this, the Pencil also moves the sheet."),
            (5, "Stroke width", "Mittlerer Strich", "Thin, middle or thick (Dünner, Mittlerer, Dicker Strich)."),
            (6, "Toolbar to the other side", "Leiste auf die andere Seite", "Landscape only; remembered on the "
                                                                           "iPad, e.g. for left-handers."),
            (7, "Full screen", "Vollbild", "Only the sheet; one button leads back (Vollbild verlassen)."),
            (8, "Undo / Redo", "Zurück", "Up to 20 steps (Zurück / Vor); the small number shows how many remain."),
            (9, "Pen colours", "Weitere Farbe", "Four presets — Orange, Hell (light), Blau, Grün — and a colour "
                                               "picker for any other colour."),
        ],
        "geschieht": "A double tap on Apple Pencil (2nd generation) switches between the current tool and the "
                     "eraser. The sheet keeps its size and fits the screen; turning the iPad does not lose the "
                     "drawing or the undo steps.",
        "grenze": "Fingers cannot draw. If the chosen layer is hidden, nothing is drawn — the sheet says so and "
                  "offers «Einblenden» (show it).",
        "geplant": [("A switch «Mit dem Finger zeichnen» (draw with the finger), default off; with the Pencil, "
                     "the finger keeps moving and zooming.", "141")],
        "quelle": "Zeichnen/Zeichenflaeche.swift · Zeichenleinwand.swift · Leiste/Leiste.swift · Leistenwahl.swift",
        "notiz": "The drawing sheet: Pencil only, pen and two erasers, pan-and-zoom hand, three stroke widths, "
                 "20 undo steps, four pen colours and a colour picker.",
    },
    {
        "kurz": "04-layers", "titel": "Layers and underlay (Ebenen)",
        "hilfe": "Each layer is a variant. Only what is visible goes out.",
        "bild": bild_ebenen, "bild_breite": 470,
        "teile": [
            (1, "Add layer", "Ebene hinzufügen", "Up to 8 layers, named Variante A, B, C …; the new one is "
                                                 "selected."),
            (2, "Show / hide", None, "The checkbox. A hidden layer reads «ausgeblendet» and never goes with the "
                                       "sketch."),
            (3, "Layer row", "leer", "Tap to choose the layer you draw on. On the right: opacity, «leer» "
                                     "(nothing drawn) or «ausgeblendet» (hidden)."),
            (4, "Opacity", "Deckkraft", "Slider from 10 % to 100 % for the chosen layer."),
            (5, "Up, down, rename, delete", "Ebene löschen?", "Renaming (Ebene umbenennen) and deleting ask "
                                                              "first; a deleted layer cannot be undone."),
            (6, "Underlay", "Unterlage", "An image from the folder under all layers — dashed row at the "
                                         "bottom: show, hide or remove (✕). Not a layer: nothing is drawn or "
                                         "erased on it."),
            (7, "What goes with it", "Geht mit: ", "One sentence says exactly what would go out, from the same "
                                                   "rule as the sending."),
        ],
        "geschieht": "The underlay comes from «Darauf skizzieren» in the image view. It goes along with the "
                     "sketch only if it is visible and from the folder the sketch goes to; the sheet title then "
                     "reads «Skizze über … · Variante A».",
        "grenze": "At most three visible layers go as variants at once. An underlay of another shape is "
                  "stretched to the sheet, exactly as the computer will place it — the row says «gestreckt».",
        "geplant": [],
        "quelle": "Zeichnen/Ebenentafel.swift · Kern/Ebenen.swift · Kern/Blattunterlage.swift",
        "notiz": "Layers as variants (up to 8, visible ones go out), opacity, order, rename, delete — and the "
                 "underlay image that sits below them.",
    },
    {
        "kurz": "05-sending", "titel": "Placing a sketch in the folder (In die Mappe legen)",
        "hilfe": "One button sends the sketch into the project folder. Nothing is computed by itself.",
        "bild": bild_senden,
        "teile": [
            (1, "Place in folder", "In die Mappe legen", "Fixed at the foot of the side panel, under both tabs."),
            (None, "What goes", "Drei Ebenen", "The visible layers as one sketch; with «Drei Ebenen» chosen in the "
                                           "folder, each visible layer as a sketch of its own. The underlay "
                                           "goes along if it is visible."),
            (2, "Hand-over strip", "in der Mappe · noch nicht gerechnet",
             "One mark on a thread: placing (legt ab), counted megabytes, waiting for the reply, arrived "
             "(in der Mappe), or back on the iPad (nicht angekommen)."),
            (3, "Reply sentence", None, "Under the button when there is something to say — nothing drawn, "
                                        "parked because nobody answers, underlay from another folder."),
        ],
        "geschieht": "The sketch is stored as open (offen) and waits. It is computed only on request: «Rechnen "
                     "lassen» in the folder tab, or as the Sketch from iPad node in the node view on the Mac. "
                     "If the Mac is not there, the sketch stays in the parking bay and goes when it is back.",
        "grenze": "There is no note field when placing — an instruction is typed when ordering («Was soll sich "
                  "ändern?»). Without a known total size the strip says «nicht gezählt» instead of showing a "
                  "bar.",
        "geplant": [],
        "quelle": "Leiste/Mappenknopf.swift · Verbindung/Uebergabe.swift · Kern/Parkfach.swift (Flugbahn)",
        "notiz": "How a sketch leaves the iPad: one button, through the parking bay, a travelling mark in the "
                 "status line — stored as open, computed only on request.",
    },
    {
        "kurz": "06-parking-bay", "titel": "Parking bay (Parkfach)",
        "hilfe": "Every sketch passes through the parking bay first — so none is lost when the connection drops.",
        "bild": bild_parkfach,
        "teile": [
            (1, "Parked", "geparkt", "Waiting to be sent; goes by itself once the Mac answers."),
            (2, "On the way", "unterwegs", "Being sent right now."),
            (3, "Arrived", "angekommen", "In the folder over there; the thumbnail reads «drüben». Cleared from "
                                         "the list after 7 days."),
            (4, "Rejected", "abgewiesen", "Refused, with the computer's sentence; stays until you decide."),
            (5, "Uncertain", "ungewiss", "Whether it arrived is not known. With its key it is resent by itself, "
                                         "and no second file appears over there."),
            (6, "Send again / Discard", "Noch einmal senden", "Discard (Verwerfen) asks first; «Behalten» keeps "
                                                              "the sketch."),
        ],
        "geschieht": "The list opens from the parking bay button in the status line. Each entry shows the "
                     "drawing, date and time, and the reason when there is one.",
        "grenze": "The guard against sending twice lives only in the computer's memory (the last 512 keys): "
                  "after a restart over there, a resend can make a duplicate — visible and removable, whereas a "
                  "lost sketch would go unnoticed.",
        "geplant": [],
        "quelle": "Verbindung/Parkfachliste.swift · Kern/Parkfach.swift",
        "notiz": "The parking bay holds every sketch until it has arrived: parked, on the way, arrived, rejected "
                 "or uncertain — with send again and discard.",
    },
    {
        "kurz": "07-folder", "titel": "Folder tab (Mappe)",
        "hilfe": "What is in the project folder, what is computing, and what can be ordered from the iPad.",
        "bild": bild_mappe, "bild_breite": 440,
        "teile": [
            (1, "Folder name, reload", "Mappe neu laden", "The folder's name and a button that asks again."),
            (2, "What the sketch does", "Was die Skizze tut", "Check (Prüfen): invented volume is an error, "
                                                              "geometry is checked. Design (Entwerfen): "
                                                              "invented volume is the point — fast, no check, "
                                                              "blue mark."),
            (3, "Run", "Lauf abbrechen", "What is computing now. A bar only for counted steps, otherwise just "
                                         "a sign of life; cancel run asks for a stop between two steps."),
            (4, "Three variants", "Drei Varianten", "From three seeds (Drei Startwerte) or from three layers "
                                                    "(Drei Ebenen); «Drei Startwerte rechnen» orders them."),
            (5, "Images", "Bilder", "Every image with its check mark; a tap opens it full size."),
            (6, "Sketches", "Rechnen lassen", "Open, computed or discarded (offen, gerechnet, verworfen). "
                                              "Compute (Rechnen lassen) with an optional instruction, give a "
                                              "name (Namen geben), open the result (Bild ansehen). With "
                                              "«Drei Ebenen» chosen: add sketches to a row (Zur Reihe) and "
                                              "compute it («Als Ebenen-Reihe rechnen»)."),
        ],
        "geschieht": "One run at a time: while one runs, ordering waits and says so. On the Layers tab a "
                     "button leads to the running job, so cancelling is never hidden behind the other tab.",
        "grenze": "With a project folder open on the Mac, computing and naming from the iPad are refused with "
                  "a sentence — images are then made in the node view on the Mac. A discarded sketch cannot be "
                  "brought back from the iPad.",
        "geplant": [],
        "quelle": "Bilder/Mappentafel.swift · Laufanzeige.swift · Skizzenliste.swift · Bildband.swift",
        "notiz": "The folder tab: Check or Design, the running job with cancel, three variants, the image strip "
                 "and the sketch list with compute, name and rows.",
    },
    {
        "kurz": "08-image-view", "titel": "Viewing an image (Bildansicht)",
        "hilfe": "One image full size, with its check mark and what the computer says about it.",
        "bild": bild_bildansicht,
        "teile": [
            (1, "Back, name, rename", "Namen geben", "Back to the strip (Zurück zum Bildband); the pencil gives "
                                                     "the image its own name in the folder."),
            (2, "Check mark", "BESTANDEN", "Frame and stripe on the image: passed (BESTANDEN, green), failed "
                                           "(DURCHGEFALLEN, red), draft (ENTWURF — NICHT GEPRÜFT, blue); dashed "
                                           "means not measured. A missing number reads «ohne Zahl», never 0."),
            (3, "Before / after", "Wischregler", "Underlay and AI image side by side (Nebeneinander) or with a "
                                                 "slider (Wischregler)."),
            (4, "Sketch on it", "Darauf skizzieren", "Puts this image under the layers as underlay and returns "
                                                     "to the sheet."),
            (5, "How the image is read", "Wie das Bild gelesen wird", "Check or Design, right at the image."),
            (6, "What the server says", "Was der Server sagt", "Verdict, number, threshold (Schwelle), caveat "
                                                               "(Vorbehalt) and hints."),
            (7, "Variants side by side", "Varianten nebeneinander", "Three places; an empty place says it is "
                                                                    "empty."),
            (8, "Share", "Teilen", "Shares only the image with its mark burned in — the caveat travels with it."),
        ],
        "geschieht": "Portrait puts the information panel below the image — same content, other arrangement.",
        "grenze": "The iPad decides nothing about an image: colour, word, number and caveat come from the "
                  "computer. Naming is refused when the folder is on the Mac.",
        "geplant": [],
        "quelle": "Bilder/Bildansicht.swift · Bildvergleich.swift · Varianten.swift · Teilen.swift · Kern/Pruefzeichen.swift",
        "notiz": "One image full size: check mark, before/after, sketch on it, Check or Design, what the server "
                 "says, variants side by side and share with the mark.",
    },
    {
        "kurz": "09-settings-updates", "titel": "Settings and updates",
        "hilfe": "The iPad app has no settings page. A few things are remembered; updates arrive only as a "
                 "notice.",
        "bild": bild_einstellungen,
        "teile": [
            (1, "New version notice", "am Mac in Xcode aufspielen", "Under the status line when a newer version "
                                                                    "exists; checked at start and once a day; "
                                                                    "can be hidden (✕)."),
            (2, "Expiry notice", "am Mac in Xcode neu aufspielen", "From two days before the app's permission "
                                                                   "runs out."),
            (3, "Remembered", None, "The toolbar side, the paired Mac (its key in the iPad keychain) and the "
                                    "project folder field on the pairing screen."),
            (4, "Not remembered", None, "Tool and stroke start with the pen and the middle width every time."),
        ],
        "geschieht": "Installing is done on the Mac in Xcode; the notice says exactly that.",
        "grenze": "An iPad app may not replace itself — Apple allows that only through the App Store or "
                  "TestFlight. With a free Apple account the app runs seven days, then it is installed again.",
        "geplant": [("A settings page with the switch «Mit dem Finger zeichnen», default off.", "141")],
        "quelle": "Verbindung/Fassungshinweis.swift · Kern/Aktualisierung.swift · Leiste/Leistenwahl.swift",
        "notiz": "No settings page yet: what the iPad remembers, and the two notices for a new version and for "
                 "the app running out.",
    },
    {
        "kurz": "10-limits-planned", "titel": "Limits today — and what is planned",
        "hilfe": "What the iPad app cannot do yet, kept apart from what has been decided for after the demo.",
        "bild": bild_grenzen, "teile_titel": "Limits today",
        "unter": "Diagram — built today (solid) and planned (dashed); not a screen of the app.",
        "teile": [
            (None, "Pencil only", None, "Fingers move and zoom; they do not draw."),
            (None, "Never computes", None, "Every image is made elsewhere; without a paired Mac nothing leaves "
                                           "the iPad."),
            (None, "Only via the Mac", None, "Encrypted, through the Mac — no direct way to the home PC any more."),
            (None, "Folder on the Mac", None, "Computing and naming from the iPad are refused; images are made "
                                              "in the node view."),
            (None, "No note when sending", None, "The instruction is typed when ordering, not when placing."),
            (None, "No settings page", None, "See card 09."),
        ],
        "geschieht": "Order after the demo: first drawn sheets for the owner to decide on, then the build — I8 "
                     "before I9.",
        "grenze": "Nothing in the planned list exists in the app today; the cards before this one describe only "
                  "what is built.",
        "geplant": [
            ("Draw with the finger: a switch «Mit dem Finger zeichnen» in the settings, default off.", "141"),
            ("I8 · Sketch on a Visbox base: for perspective and axonometric views a light line drawing of the "
             "model from the camera, switchable to the computed base image; a locked lower layer at 60 % "
             "opacity that can be hidden and is never drawn into.", "145"),
            ("I9 · Templates per sketch type: plan, section and elevation get a true-to-scale base from the "
             "model at the chosen scale; freehand gets only a grid. The type is chosen when the sketch is "
             "created.", "145"),
            ("The iPad in floating islands with a tool wheel at the top left.", "135"),
        ],
        "quelle": "docs/ENTSCHEIDE_IPAD_2026-09-21.md (Decisions 135, 141, 145)",
        "notiz": "What the iPad app cannot do yet — and, kept apart, what is decided for after the demo: finger "
                 "drawing, I8 sketch on a Visbox base, I9 templates, tool wheel.",
    },
]


# ── HTML ────────────────────────────────────────────────────────────────────────────────────────────

def _css() -> str:
    return KT._kopf_css() + """
.leib { grid-template-columns: 720px 1fr; }
.schema { background: #0e1015; border-radius: 14px; padding: 18px; }
.schema svg { display: block; margin: 0 auto; }
.unter { color: var(--sehrleise); font-size: 15px; margin-top: 10px; }
.teil { display: grid; grid-template-columns: 34px 1fr; gap: 12px; padding: 7px 0;
  border-top: 1px solid var(--linie); font-size: 18.5px; line-height: 1.38; }
.teil:first-of-type { border-top: none; }
.nr { width: 28px; height: 28px; border-radius: 50%; background: #ffc21a; color: #12151c; font-weight: 700;
  font-size: 15px; display: flex; align-items: center; justify-content: center; margin-top: 1px; }
.nr.leer { background: transparent; border: 2px solid var(--linie); }
.teil b { font-weight: 600; }
.ui { color: var(--leise); }
.geplant { margin-top: 18px; border: 2.5px dashed #ffc21a; border-radius: 14px; padding: 18px 22px; }
.geplant h2 { font-size: 15px; letter-spacing: .12em; text-transform: uppercase; color: #ffc21a;
  font-weight: 700; margin-bottom: 8px; }
.geplant li { font-size: 18px; line-height: 1.4; margin: 6px 0 0 22px; color: var(--leise); }
.geplant .ent { font-family: 'PlexMono', monospace; font-size: 14px; color: var(--sehrleise); }
"""


def _teile_html(k: dict) -> str:
    zeilen = []
    for nr, en, ui, satz in k["teile"]:
        marke = f'<span class="nr">{nr}</span>' if nr else '<span class="nr leer"></span>'
        name = f"<b>{_e(en)}</b>"
        if ui and ui.strip() != en and not ui.endswith(" ") and ui not in satz:
            name += f' <span class="ui">({_e(ui)})</span>'
        zeilen.append(f'<div class="teil">{marke}<div>{name} — {_e(satz)}</div></div>')
    return "".join(zeilen)


def _geplant_html(k: dict) -> str:
    if not k["geplant"]:
        return ""
    punkte = "".join(f'<li>{_e(t)} <span class="ent">Decision {_e(e)}</span></li>' for t, e in k["geplant"])
    return (f'<div class="geplant"><h2>Planned — decided, not built</h2><ul>{punkte}</ul></div>')


UNTER = "Drawn schematic — not a screenshot. Labels as on screen (German); numbers point to the list."


def karte_html(k: dict, nummer: int) -> str:
    breite = k.get("bild_breite", 684)
    zweites = (f'<div class="block" style="margin-top:18px"><h2>How the iPad works with the Mac</h2>'
               f'{k["bild2"]()}</div>') if k.get("bild2") else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<style>{_css()}</style></head><body><div class="karte">
<div class="oben"><span class="nummer">{nummer:02d} / {len(KARTEN) - 1:02d}</span>
<span class="gruppe" style="color:#6fb3d2">{_e(GRUPPE)}</span></div>
<h1>{_e(k["titel"])}</h1><div class="hilfe">{_e(k["hilfe"])}</div>
<div class="leib"><div><div class="schema">{k["bild"]().replace('width="100%"', f'width="{breite}"')}</div>
<div class="unter">{_e(k.get("unter", UNTER))}</div>
{zweites}</div>
<div><div class="block"><h2>{_e(k.get("teile_titel", "On screen"))}</h2>{_teile_html(k)}</div>
<div class="zwei">
<div class="block"><h2>What happens</h2><p>{_e(k["geschieht"])}</p></div>
<div class="block grenze"><h2>Honest limit</h2><p>{_e(k["grenze"])}</p></div>
</div>{_geplant_html(k)}</div></div>
<div class="fuss"><span>Source: {_e(k["quelle"])}</span><span>Visbox iPad · {_e(BLATT)}</span></div>
</div></body></html>"""


def karten() -> list[tuple[str, str, str, str]]:
    """(kurzname, titel, notiz, html) je Karte."""
    return [(k["kurz"], k["titel"], k["notiz"], karte_html(k, i)) for i, k in enumerate(KARTEN)]


# ── das Blatt ───────────────────────────────────────────────────────────────────────────────────────

def markdown() -> str:
    """``docs/IPAD_ERKLAERT.en.md`` — aus denselben Daten wie die Karten."""
    z = ["# Visbox on the iPad — what each part does", "",
         "*Source of the board section «Visbox · iPad» (cards `" + DATUM + "-ipad-NN-*`), written by "
         "`tools/ipad_tafel.py --markdown`. Do not edit by hand — change the tool and regenerate.*", "",
         "Only what is in the code under `ipad/Visbox.swiftpm` is described. Every on-screen label in "
         "parentheses is the German wording of the app; a probe (`tests/test_ipad_tafel.py`) finds each one "
         "in the Swift sources. Planned items stand only under **Planned — decided, not built**, each with "
         "the decision that settles it. The pictures on the cards are drawn schematics, not screenshots.", ""]
    for i, k in enumerate(KARTEN):
        z += [f"## {i:02d} · {k['titel']}", "", k["hilfe"], "", f"**{k.get('teile_titel', 'On screen')}**", ""]
        for nr, en, ui, satz in k["teile"]:
            vor = f"{nr}. " if nr else "- "
            name = f"**{en}**"
            if ui and ui.strip() != en and not ui.endswith(" ") and ui not in satz:
                name += f" ({ui})"
            z.append(f"{vor}{name} — {satz}")
        z += ["", f"**What happens.** {k['geschieht']}", "", f"**Honest limit.** {k['grenze']}", ""]
        if k["geplant"]:
            z += ["**Planned — decided, not built**", ""]
            z += [f"- {t} *(Decision {e})*" for t, e in k["geplant"]]
            z.append("")
        z += [f"*Source: {k['quelle']}*", ""]
    return "\n".join(z)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ausgabe", default=str(Path(tempfile.gettempdir()) / "ipad-tafel"),
                    help="Ordner für HTML, PNG und JSON der Tafel (nicht im Repo).")
    ap.add_argument("--karte", default=None, help="Nur diese Karte (Teil des Kurznamens, z. B. 03).")
    ap.add_argument("--nur-html", action="store_true", help="Nur HTML und JSON, kein Bild (ohne Chromium).")
    ap.add_argument("--chrome", default=None, help="Pfad zum Chromium, sonst gesucht.")
    ap.add_argument("--markdown", default=None, help=f"Nur das Blatt schreiben (z. B. {BLATT}).")
    a = ap.parse_args(argv)

    if a.markdown:
        Path(a.markdown).write_text(markdown(), encoding="utf-8")
        print(a.markdown)
        return 0
    ziel = Path(a.ausgabe).resolve()
    ziel.mkdir(parents=True, exist_ok=True)
    auswahl = [c for c in karten() if a.karte is None or a.karte in c[0]]
    if not auswahl:
        print(f"Keine Karte passt zu «{a.karte}».", file=sys.stderr)
        return 2
    chrome = None if a.nur_html else KT.finde_chrome(a.chrome)
    if not a.nur_html and chrome is None:
        print("Kein Chromium gefunden — mit --chrome angeben oder --nur-html.", file=sys.stderr)
        return 3
    for kurz, titel, notiz, inhalt in auswahl:
        name = f"{DATUM}-ipad-{kurz}"
        (ziel / f"{name}.html").write_text(inhalt, encoding="utf-8")
        (ziel / f"{name}.json").write_text(
            json.dumps({"titel": titel, "gruppe": GRUPPE, "notiz": notiz}, ensure_ascii=False), encoding="utf-8")
        if chrome:
            groesse = KT.rendere(ziel / f"{name}.html", ziel / f"{name}.png", chrome, hoehe=1700)
            kb = (ziel / f"{name}.png").stat().st_size // 1024
            print(f"{name}.png  {groesse[0]}×{groesse[1]}  {kb} KB")
        else:
            print(f"{name}.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
