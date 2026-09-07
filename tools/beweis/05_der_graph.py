#!/usr/bin/env python3
"""BEWEIS 05 — Der Node-Tree selbst (``graph.py``, ``kette.py``): Die Standardkette ist
ein gerichteter Graph mit fester Rechenreihenfolge, und ihr Zwischenspeicher rechnet
nach einer Änderung GENAU die Knoten neu, deren Inhalt sich geändert hat — gezählt an
vier echten Läufen mit Attrappen, nicht behauptet.

Was bewiesen wird
-----------------
1. **Der Graph.** ``kette.baue_kette`` liefert einen ``graph.Graph`` mit vier Knoten;
   ``Graph.topologische_reihenfolge`` gibt die Rechenreihenfolge (Kahn, bei Gleichrang
   die kleinste ID zuerst). Die QA hängt an ZWEI Vorgängern — Slot 0 ist das Soll aus
   dem Multipass, Slot 1 das Ist aus dem Render. Darum ist die Kette ein Graph und
   keine Liste.
2. **Der Zwischenspeicher.** ``kette.fuehre_aus`` bildet je Knoten einen Inhalts-Hash
   aus Art, Parametern, Vorgänger-Hashes und dem INHALT der Eingabedatei
   (``graph.inhalts_hash``). Ein Treffer im ``graph.ArtefaktCache`` heisst: Der
   Ausführer wird gar nicht gerufen. Es gibt keine programmierte Invalidierung —
   ein geänderter Vorgänger ergibt schlicht einen anderen Schlüssel.

Derselbe Graph läuft viermal, mit ZÄHLENDEN Attrappen an Stelle von ifcopenshell,
Blender und Bildmodell (dieselbe Werkbank wie in ``tests/test_kette.py``):

    Lauf 1  erster Durchlauf        alles rechnet                 4 gerechnet, 0 Speicher
    Lauf 2  nur Prompt geändert     Geometrie + Multipass NICHT   2 gerechnet, 2 Speicher
    Lauf 3  unverändert             nichts rechnet                0 gerechnet, 4 Speicher
    Lauf 4  Geometrie geändert      alles rechnet                 4 gerechnet, 0 Speicher

«Geometrie geändert» heisst: dieselbe IFC-Datei unter demselben Pfad, aber anderer
Inhalt (``make_test_ifc.erzeuge_ifc`` mit ``hochbau=True`` statt des Quaders). Der
Cache hängt am Inhalt, nicht am Namen — ein umbenannter Ordner verwürfe sonst alles,
und eine überschriebene Datei ergäbe das Bild von gestern zur Geometrie von heute.

Warum Attrappen — und warum das trotzdem ein Beweis ist
-------------------------------------------------------
Was ein Knoten TUT, weiss ``graph.py`` nicht; es steuert nur Reihenfolge, Datenfluss
und Wiederverwendung. Genau das wird hier geprüft. Die Attrappen schreiben echte, wenn
auch winzige Dateien (der Cache verwirft Einträge, deren zugesagte Datei fehlt), und
sie ZÄHLEN jeden Aufruf. Der Beweis ist die Aufrufzahl, nicht die Laufzeit: «zweiter
Lauf war schneller» erklärt auch ein warmer Dateisystem-Cache. Was die echten Knoten
leisten, zeigen die Beweise 01–04.

Woran man es im Bild sieht
--------------------------
Keine Schrift im Bild (Regel 2); die Bedeutung liegt in Anordnung, Farbe und
Dateiname.

``01_graph_…png`` — der DAG. Kästen von links nach rechts in der topologischen
Reihenfolge (die Reihenfolge steht im Dateinamen); Spalte = längster Weg von der
Quelle. Jeder Kasten trägt oben ein Kopfband in seiner Kennfarbe:

    Braun      geometrie    (IFC → glb, Torwächter)
    Stahlblau  multipass    (Blender: Tiefe, Beauty, Material-ID)
    Violett    render       (Bildmodell, ControlNet)
    Grün       qa           (Geometrietreue Ist gegen Soll)

Dunkle Linien mit Pfeilspitze sind die Kanten. Der Kasten ganz rechts (qa) hat ZWEI
eingehende Pfeile: einen geraden von links (render) und einen, der über eine Schleife
oberhalb der Kästen vom multipass kommt. Unter jedem Kasten ein Farbstreifen aus acht
Feldern — der «Fingerabdruck» des Inhalts-Hashes (die ersten 24 Bytes des sha256, je
drei als eine Farbe). Er ist keine Deutung, sondern der Hash selbst in Farbe: Gleicher
Streifen = gleicher Schlüssel = Cache-Treffer möglich.

``02_lauf-1_…`` bis ``05_lauf-4_…png`` — derselbe Graph nach jedem Lauf. Der Rumpf
jedes Kastens ist nun gefärbt:

    Orange   gerechnet — der Ausführer wurde in diesem Lauf gerufen
    Blau     aus dem Speicher — Cache-Treffer, der Ausführer wurde NICHT gerufen
    (Grau    übersprungen, Rot gescheitert — kommen hier nicht vor; wären sie da,
             stünden sie im Bild, nicht im Docstring)

Unter dem Fingerabdruck kleine dunkle Quadrate: die KUMULIERTE Zahl der
Ausführeraufrufe für diesen Knoten seit Lauf 1. Das ist die eigentliche Messung. Man
sieht: Nach Lauf 2 haben geometrie und multipass weiterhin EIN Quadrat (sie liefen
nicht), render und qa zwei. Nach Lauf 3 ändert sich kein einziges Quadrat. Nach Lauf 4
hat jeder Knoten ein Quadrat mehr. Die Fingerabdrücke zeigen dasselbe von der anderen
Seite: Lauf 2 ändert nur die Streifen von render und qa, Lauf 3 keinen, Lauf 4 alle.
Die Zahl der gerechneten und aus dem Speicher geholten Knoten steht im Dateinamen —
aus ``fuehre_aus`` ausgelesen, nicht aus der Erinnerung.

``06_vier-laeufe_…png`` — die vier Läufe untereinander, links je Zeile so viele
Quadrate wie die Laufnummer, rechts zwei Balken: Orange = gerechnet, Blau = aus dem
Speicher (Länge = Anzahl Knoten). Im Dateinamen die Gesamtaufrufe je Knoten über alle
vier Läufe — für die Standardkette 2 / 2 / 3 / 3.

``07_matrix_…png`` — dieselbe Aussage als Tafel: Zeilen = Läufe (Quadrate links),
Spalten = Knoten in Rechenreihenfolge (Kennfarbe oben), Zelle = Orange oder Blau.

Was das Gerät braucht
---------------------
Nichts. Dieser Beweis läuft vollständig ohne GPU, ohne Blender und ohne ``.venv-ifc``
— Ablaufkern und Zwischenspeicher sind reine stdlib (``graph.py``, Modulkopf), und die
Testgeometrie schreibt ``make_test_ifc`` als STEP-Text. Kein Teil wird übersprungen.

Aufruf:
    python3 tools/beweis/05_der_graph.py [ziel_verzeichnis]

Ohne Argument schreibt es nach ``build/beweis/05_der_graph/``. Rückgabe 1, wenn das
gezählte Muster der vier Läufe der Behauptung widerspricht — das wäre kein «nicht
gemessen», sondern ein Befund gegen den Zwischenspeicher.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))
sys.path.insert(0, str(WURZEL / "tools"))

import make_test_ifc  # noqa: E402
from aiimaging import bildschreiben, kette  # noqa: E402
from aiimaging.graph import ArtefaktCache, Graph  # noqa: E402

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "05_der_graph"

# --------------------------------------------------------------------------------------
# Farbsprache — jede Farbe hat genau eine Bedeutung, siehe Docstring
# --------------------------------------------------------------------------------------
KENNFARBE = {
    kette.KNOTEN_GEOMETRIE: (140, 100, 60),     # Braun
    kette.KNOTEN_MULTIPASS: (70, 100, 150),     # Stahlblau
    kette.KNOTEN_RENDER: (130, 80, 150),        # Violett
    kette.KNOTEN_QA: (60, 150, 70),             # Grün
}
#: Für Knoten, die nicht zur Standardkette gehören — der Zeichner soll an jedem Graphen
#: funktionieren, nicht nur an dem, den er heute bekommt.
ERSATZ_KENNFARBEN = ((180, 130, 40), (40, 140, 140), (160, 60, 90), (90, 90, 90))

FARBE_GERECHNET = (230, 120, 40)         # Orange
FARBE_SPEICHER = (80, 130, 200)          # Blau
FARBE_UEBERSPRUNGEN = (200, 200, 200)    # Grau
FARBE_FEHLER = (190, 60, 50)             # Rot
FARBE_NEUTRAL = (225, 225, 225)          # Rumpf im Strukturbild: kein Lauf, kein Zustand
FARBE_KANTE = (60, 60, 60)
FARBE_ZAEHLER = (40, 40, 40)
FARBE_LEINWAND = (245, 245, 245)
FARBE_RAHMEN = (110, 110, 110)

RAND = 24
BOX_B, BOX_H, KOPF = 132, 72, 16
SPALTE = BOX_B + 76                      # Abstand Kastenanfang → Kastenanfang
FUSS = 46                                # Platz unter dem Kasten: Fingerabdruck + Zähler
ZEILE = BOX_H + FUSS + 24
SCHLEIFE_ABSTAND = 12                    # Höhe je Schleifenbahn oberhalb der Kästen
FINGER_FELDER = 8
ZAEHLER_KANTE, ZAEHLER_FUGE = 8, 4


# --------------------------------------------------------------------------------------
# Werkbank — zählende Attrappen, die echte Dateien schreiben
# --------------------------------------------------------------------------------------

class Werkbank:
    """Ersatz-Ausführer für alle vier Knotenarten, mit Aufrufzähler.

    Die Dateien sind winzig, aber echt: ``fuehre_aus`` verwirft einen Cache-Eintrag,
    dessen zugesagte Datei fehlt. Eine Attrappe, die nur Pfade behauptet, ergäbe bei
    jedem Lauf einen Fehltreffer — und das Bild zeigte das Gegenteil dessen, was gilt.
    """

    BBOX_HAUS = [[0.0, 0.0, 0.0], [8.0, 5.0, 3.0]]

    def __init__(self) -> None:
        self.aufrufe: Counter = Counter()

    def tabelle(self) -> dict:
        return {
            kette.ART_GEOMETRIE: self.geometrie,
            kette.ART_MULTIPASS: self.multipass,
            kette.ART_RENDER: self.render,
            kette.ART_QA: self.qa,
        }

    def geometrie(self, *, knoten, eingaben, out_dir):
        self.aufrufe[kette.KNOTEN_GEOMETRIE] += 1
        glb = out_dir / "modell.glb"
        quelle = knoten.params.get("ifc_path") or knoten.params.get("glb_path")
        glb.write_text(f"glb aus {Path(quelle).name}", encoding="utf-8")
        return {"glb_path": str(glb), "up_axis": "Y", "bbox": self.BBOX_HAUS}

    def multipass(self, *, knoten, eingaben, out_dir):
        self.aufrufe[kette.KNOTEN_MULTIPASS] += 1
        tiefe = out_dir / "tiefe_norm.png"
        tiefe.write_text("tiefe", encoding="utf-8")
        return {"status": "ok", "depth_png": str(tiefe),
                "aufloesung": knoten.params["aufloesung"]}

    def render(self, *, knoten, eingaben, out_dir):
        self.aufrufe[kette.KNOTEN_RENDER] += 1
        bild = out_dir / "bild.png"
        bild.write_text(f"bild zu {knoten.params['prompt']}", encoding="utf-8")
        return {"status": "ok", "bild_png": str(bild)}

    def qa(self, *, knoten, eingaben, out_dir):
        self.aufrufe[kette.KNOTEN_QA] += 1
        return {"status": "ok", "bestanden": True, "score": 0.91}


# --------------------------------------------------------------------------------------
# Zeichenhilfen — achsparallel, damit der stdlib-Schreiber genügt
# --------------------------------------------------------------------------------------

def _rechteck(px, breite, hoehe, x0, y0, x1, y1, farbe) -> None:
    xa, xb = sorted((max(0, int(round(x0))), min(breite, int(round(x1)))))
    ya, yb = sorted((max(0, int(round(y0))), min(hoehe, int(round(y1)))))
    for y in range(ya, yb):
        px[y * breite + xa:y * breite + xb] = [farbe] * (xb - xa)


def _rahmen(px, breite, hoehe, x0, y0, x1, y1, farbe, dicke=1) -> None:
    _rechteck(px, breite, hoehe, x0, y0, x1, y0 + dicke, farbe)
    _rechteck(px, breite, hoehe, x0, y1 - dicke, x1, y1, farbe)
    _rechteck(px, breite, hoehe, x0, y0, x0 + dicke, y1, farbe)
    _rechteck(px, breite, hoehe, x1 - dicke, y0, x1, y1, farbe)


def _linie(px, breite, hoehe, x0, y0, x1, y1, farbe, dicke=2) -> None:
    """Waagrechte oder senkrechte Strecke. Schräge Kanten braucht dieses Layout nicht."""
    h = dicke / 2
    if y0 == y1:
        _rechteck(px, breite, hoehe, min(x0, x1), y0 - h, max(x0, x1), y0 + h, farbe)
    elif x0 == x1:
        _rechteck(px, breite, hoehe, x0 - h, min(y0, y1), x0 + h, max(y0, y1), farbe)
    else:
        raise ValueError(f"nur achsparallele Strecken: ({x0},{y0})→({x1},{y1})")


def _pfeilspitze(px, breite, hoehe, x, y, richtung: str, farbe, groesse=7) -> None:
    """Gefülltes Dreieck mit Spitze in (x, y); ``richtung`` ist, wohin es zeigt."""
    for d in range(groesse + 1):
        halb = d * 0.6
        if richtung == "rechts":
            _rechteck(px, breite, hoehe, x - d, y - halb, x - d + 1, y + halb + 1, farbe)
        elif richtung == "unten":
            _rechteck(px, breite, hoehe, x - halb, y - d, x + halb + 1, y - d + 1, farbe)
        else:
            raise ValueError(richtung)


def _fingerabdruck(hash_hex: str) -> list[tuple[int, int, int]]:
    """Acht Farben aus den ersten 24 Bytes des Hashes. Auf 64..255 gehoben, damit kein
    Feld schwarz wird — Gleichheit bleibt Gleichheit, Ungleichheit bleibt sichtbar."""
    roh = bytes.fromhex(hash_hex[: FINGER_FELDER * 6])
    return [tuple(64 + b * 191 // 255 for b in roh[i:i + 3])
            for i in range(0, len(roh), 3)]


def _zaehler(px, breite, hoehe, x, y, n: int, farbe=FARBE_ZAEHLER) -> None:
    for i in range(n):
        x0 = x + i * (ZAEHLER_KANTE + ZAEHLER_FUGE)
        _rechteck(px, breite, hoehe, x0, y, x0 + ZAEHLER_KANTE, y + ZAEHLER_KANTE, farbe)


def _zustandsfarbe(eintrag: dict | None):
    if eintrag is None:
        return FARBE_NEUTRAL
    if eintrag["aus_cache"]:
        return FARBE_SPEICHER
    if eintrag["status"] == kette.STATUS_UEBERSPRUNGEN:
        return FARBE_UEBERSPRUNGEN
    if eintrag["status"] != kette.STATUS_OK:
        return FARBE_FEHLER
    return FARBE_GERECHNET


# --------------------------------------------------------------------------------------
# Layout — Spalte aus dem längsten Weg, Zeile aus der Reihenfolge
# --------------------------------------------------------------------------------------

def _layout(graph: Graph, reihenfolge: list[str]) -> tuple[dict, list]:
    """Position je Knoten und die Kanten, die eine Schleife brauchen.

    Spalte = längster Weg von einer Quelle (jeder Vorgänger steht links). Innerhalb
    einer Spalte in der Rechenreihenfolge von oben nach unten. Eine Kante zwischen
    Nachbarspalten auf gleicher Zeile wird gerade gezeichnet; jede andere führt über
    eine Bahn oberhalb der Kästen — so bleibt der Bereich unter den Kästen frei für
    Fingerabdruck und Zähler.
    """
    tiefe: dict[str, int] = {}
    for kid in reihenfolge:
        vor = graph.vorgaenger(kid)
        tiefe[kid] = 0 if not vor else 1 + max(tiefe[v] for v in vor)
    belegt: Counter = Counter()
    zeile: dict[str, int] = {}
    for kid in reihenfolge:
        zeile[kid] = belegt[tiefe[kid]]
        belegt[tiefe[kid]] += 1

    schleifen = []
    for kid in reihenfolge:
        for v in dict.fromkeys(graph.vorgaenger(kid)):
            if not (tiefe[kid] == tiefe[v] + 1 and zeile[kid] == zeile[v]):
                schleifen.append((v, kid))

    n_spalten = 1 + max(tiefe.values())
    n_zeilen = max(belegt.values())
    oben = RAND + len(schleifen) * SCHLEIFE_ABSTAND + 10
    pos = {kid: (RAND + tiefe[kid] * SPALTE, oben + zeile[kid] * ZEILE)
           for kid in reihenfolge}
    masse = {
        "breite": 2 * RAND + (n_spalten - 1) * SPALTE + BOX_B,
        "hoehe": oben + (n_zeilen - 1) * ZEILE + BOX_H + FUSS + RAND,
    }
    return {"pos": pos, "tiefe": tiefe, **masse}, schleifen


def _kennfarbe(kid: str, index: int):
    return KENNFARBE.get(kid, ERSATZ_KENNFARBEN[index % len(ERSATZ_KENNFARBEN)])


def zeichne_graph(graph: Graph, reihenfolge: list[str], *,
                  lauf: dict | None = None, aufrufe: Counter | None = None,
                  hashes: dict[str, str] | None = None):
    """Der Graph als Bild. Ohne ``lauf`` nur die Struktur (Rumpf neutral)."""
    lay, schleifen = _layout(graph, reihenfolge)
    b, h = lay["breite"], lay["hoehe"]
    px = [FARBE_LEINWAND] * (b * h)
    pos = lay["pos"]

    # Kanten zuerst, damit die Kästen darüber liegen.
    for kid in reihenfolge:
        x1, y1 = pos[kid]
        for v in dict.fromkeys(graph.vorgaenger(kid)):
            if (v, kid) in schleifen:
                continue
            x0, y0 = pos[v]
            ym = y0 + BOX_H // 2
            _linie(px, b, h, x0 + BOX_B, ym, x1 - 1, ym, FARBE_KANTE)
            _pfeilspitze(px, b, h, x1 - 1, ym, "rechts", FARBE_KANTE)
    for i, (v, kid) in enumerate(schleifen):
        bahn = RAND + i * SCHLEIFE_ABSTAND
        x0, y0 = pos[v]
        x1, y1 = pos[kid]
        xa, xb = x0 + BOX_B // 2, x1 + BOX_B // 2
        _linie(px, b, h, xa, y0, xa, bahn, FARBE_KANTE)
        _linie(px, b, h, xa, bahn, xb, bahn, FARBE_KANTE)
        _linie(px, b, h, xb, bahn, xb, y1 - 1, FARBE_KANTE)
        _pfeilspitze(px, b, h, xb, y1 - 1, "unten", FARBE_KANTE)

    for i, kid in enumerate(reihenfolge):
        x, y = pos[kid]
        eintrag = None if lauf is None else lauf["knoten"][kid]
        _rechteck(px, b, h, x, y, x + BOX_B, y + BOX_H, _zustandsfarbe(eintrag))
        _rechteck(px, b, h, x, y, x + BOX_B, y + KOPF, _kennfarbe(kid, i))
        _rahmen(px, b, h, x, y, x + BOX_B, y + BOX_H, FARBE_RAHMEN)

        hash_hex = None if hashes is None else hashes.get(kid)
        if hash_hex:
            feld = BOX_B / FINGER_FELDER
            for j, farbe in enumerate(_fingerabdruck(hash_hex)):
                _rechteck(px, b, h, x + j * feld, y + BOX_H + 6,
                          x + (j + 1) * feld, y + BOX_H + 16, farbe)
        if aufrufe is not None:
            _zaehler(px, b, h, x, y + BOX_H + 24, aufrufe[kid])
    return px, b, h


def zeichne_uebersicht(tafeln: list[tuple[list, int, int]], laeufe: list[dict],
                       n_knoten: int):
    """Die Läufe untereinander; links die Laufnummer als Quadrate, rechts zwei Balken."""
    fuge, links, rechts = 10, 60, 160
    tb = max(t[1] for t in tafeln)
    b = links + tb + rechts
    h = sum(t[2] for t in tafeln) + fuge * (len(tafeln) - 1)
    px = [FARBE_LEINWAND] * (b * h)
    y = 0
    balken_max = rechts - 40
    for i, ((tpx, tbr, th), lauf) in enumerate(zip(tafeln, laeufe)):
        for zy in range(th):
            px[(y + zy) * b + links:(y + zy) * b + links + tbr] = tpx[zy * tbr:(zy + 1) * tbr]
        _zaehler(px, b, h, 16, y + th // 2 - ZAEHLER_KANTE // 2, i + 1)
        xb = links + tb + 20
        ym = y + th // 2
        for k, (anzahl, farbe) in enumerate(((lauf["gerechnet"], FARBE_GERECHNET),
                                             (lauf["cache_treffer"], FARBE_SPEICHER))):
            laenge = balken_max * anzahl / n_knoten
            y0 = ym - 14 + k * 16
            _rechteck(px, b, h, xb, y0, xb + laenge, y0 + 12, farbe)
            _rahmen(px, b, h, xb, y0, xb + balken_max, y0 + 12, FARBE_RAHMEN)
        if i < len(tafeln) - 1:
            _rechteck(px, b, h, 0, y + th, b, y + th + fuge, (215, 215, 215))
        y += th + fuge
    return px, b, h


def zeichne_matrix(laeufe: list[dict], reihenfolge: list[str]):
    """Zeilen = Läufe, Spalten = Knoten in Rechenreihenfolge, Zelle = Zustand."""
    zelle, fuge, links, oben = 48, 6, 70, 22
    b = links + len(reihenfolge) * (zelle + fuge) + RAND
    h = oben + len(laeufe) * (zelle + fuge) + RAND
    px = [FARBE_LEINWAND] * (b * h)
    for j, kid in enumerate(reihenfolge):
        x = links + j * (zelle + fuge)
        _rechteck(px, b, h, x, 6, x + zelle, 6 + 10, _kennfarbe(kid, j))
    for i, lauf in enumerate(laeufe):
        y = oben + i * (zelle + fuge)
        _zaehler(px, b, h, 10, y + zelle // 2 - ZAEHLER_KANTE // 2, i + 1)
        for j, kid in enumerate(reihenfolge):
            x = links + j * (zelle + fuge)
            _rechteck(px, b, h, x, y, x + zelle, y + zelle,
                      _zustandsfarbe(lauf["knoten"][kid]))
            _rahmen(px, b, h, x, y, x + zelle, y + zelle, FARBE_RAHMEN)
    return px, b, h


# --------------------------------------------------------------------------------------
# Der Lauf
# --------------------------------------------------------------------------------------

#: Die vier Läufe: Name, was sich gegenüber dem vorigen ändert, erwartetes Muster
#: (welche Knoten aus dem Speicher kommen MÜSSEN). Das Muster ist die Behauptung; die
#: Bilder zeigen die Messung; die Rückgabe sagt, ob beide übereinstimmen.
LAEUFE = (
    ("erster-durchlauf", "Morgenlicht, klare Sicht", "quader", frozenset()),
    ("nur-prompt-geaendert", "Abendstimmung, warmes Licht", "quader",
     frozenset({kette.KNOTEN_GEOMETRIE, kette.KNOTEN_MULTIPASS})),
    ("unveraendert", "Abendstimmung, warmes Licht", "quader",
     frozenset({kette.KNOTEN_GEOMETRIE, kette.KNOTEN_MULTIPASS,
                kette.KNOTEN_RENDER, kette.KNOTEN_QA})),
    ("geometrie-geaendert", "Abendstimmung, warmes Licht", "hochbau", frozenset()),
)


def schreibe_geometrie(ifc: Path, gestalt: str) -> None:
    """Dieselbe Datei, wahlweise als Quader oder als gegliederter Hochbau — beides
    synthetisch aus ``make_test_ifc`` (Regel 3). Nur bei Wechsel neu geschrieben, damit
    «unverändert» wirklich unverändert heisst — auch wenn ein Neuschreiben mit gleichem
    Inhalt den Hash ohnehin nicht änderte."""
    marke = ifc.with_suffix(".gestalt")
    if marke.exists() and marke.read_text(encoding="utf-8") == gestalt:
        return
    make_test_ifc.erzeuge_ifc(ifc, mit_gelaende=True, hochbau=(gestalt == "hochbau"))
    marke.write_text(gestalt, encoding="utf-8")


def main() -> int:
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else ZIEL_VORGABE
    ziel.mkdir(parents=True, exist_ok=True)
    arbeit = ziel / "_arbeit"
    arbeit.mkdir(exist_ok=True)
    geschrieben: list[Path] = []
    nr = 0

    def schreibe(stamm: str, px, b, h) -> None:
        nonlocal nr
        nr += 1
        pfad = ziel / f"{nr:02d}_{stamm}.png"
        bildschreiben.schreibe_farb_png(pfad, px, b, h)
        geschrieben.append(pfad)

    ifc = arbeit / "testbau.ifc"
    for alt in (ifc, ifc.with_suffix(".gestalt")):
        alt.unlink(missing_ok=True)
    cache = ArtefaktCache(arbeit / "cache")
    cache.leere()
    werkbank = Werkbank()

    # Bild 1: die Struktur, vor jedem Lauf. Hashes gibt es erst nach einem Lauf — der
    # Fingerabdruck kommt darum aus Lauf 1, der Graph selbst ist derselbe.
    schreibe_geometrie(ifc, LAEUFE[0][2])
    graph = kette.baue_kette(ifc_path=str(ifc), prompt=LAEUFE[0][1])
    reihenfolge = graph.topologische_reihenfolge()
    befunde = [b for b in kette.pruefe_kette(graph) if b["schwere"] == "error"]
    if befunde:
        print(f"Graph nicht verdrahtet: {befunde}", file=sys.stderr)
        return 1

    laeufe: list[dict] = []
    tafeln = []
    widersprueche: list[str] = []
    for i, (name, prompt, gestalt, erwartet_speicher) in enumerate(LAEUFE, start=1):
        schreibe_geometrie(ifc, gestalt)
        graph = kette.baue_kette(ifc_path=str(ifc), prompt=prompt)
        ergebnis = kette.fuehre_aus(graph, cache=cache, ausfuehrer=werkbank.tabelle(),
                                    out_dir=arbeit / "out", pruefe_verdrahtung=True)
        laeufe.append(ergebnis)
        hashes = {kid: e["hash"] for kid, e in ergebnis["knoten"].items()}
        if i == 1:
            px, b, h = zeichne_graph(graph, reihenfolge, hashes=hashes)
            schreibe("graph_topologische-ordnung_" + "-".join(reihenfolge)
                     + f"_knoten-{len(graph)}_kanten-"
                     f"{sum(len(set(graph.vorgaenger(k))) for k in reihenfolge)}",
                     px, b, h)

        px, b, h = zeichne_graph(graph, reihenfolge, lauf=ergebnis,
                                 aufrufe=Counter(werkbank.aufrufe), hashes=hashes)
        tafeln.append((px, b, h))
        schreibe(f"lauf-{i}_{name}_gerechnet-{ergebnis['gerechnet']}"
                 f"_speicher-{ergebnis['cache_treffer']}", px, b, h)

        ist_speicher = {kid for kid, e in ergebnis["knoten"].items() if e["aus_cache"]}
        if ergebnis["status"] != kette.STATUS_OK or ist_speicher != erwartet_speicher:
            widersprueche.append(
                f"Lauf {i} ({name}): status={ergebnis['status']!r}, aus dem Speicher "
                f"{sorted(ist_speicher)}, erwartet {sorted(erwartet_speicher)}")

    px, b, h = zeichne_uebersicht(tafeln, laeufe, len(reihenfolge))
    schreibe("vier-laeufe_uebereinander_aufrufe-" + "_".join(
        f"{kid}-{werkbank.aufrufe[kid]}" for kid in reihenfolge), px, b, h)

    px, b, h = zeichne_matrix(laeufe, reihenfolge)
    schreibe("matrix_laeufe-gegen-knoten_gerechnet-" + "-".join(
        str(l["gerechnet"]) for l in laeufe) + "_speicher-" + "-".join(
        str(l["cache_treffer"]) for l in laeufe), px, b, h)

    for p in geschrieben:
        print(p)

    if widersprueche:
        print("BEHAUPTUNG WIDERLEGT — Befund gegen den Zwischenspeicher, nicht gegen "
              "die Szene:\n  " + "\n  ".join(widersprueche), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
