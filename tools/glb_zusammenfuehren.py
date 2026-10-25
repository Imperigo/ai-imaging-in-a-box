#!/usr/bin/env python3
"""Zwei glb zu einer — das Situationsmodell und die Umgebungsbauten desselben Orts (Vorbereitung 25.10.2026).

Am Heim-PC liegt neben dem Situationsmodell eine zweite IFC mit den Umgebungsbauten in echter Höhe. Beide werden
mit **demselben Versatz** neutralisiert (``tools/ifc_neutralisieren.py --versatz-schreiben``/``--versatz-lesen``)
und je zur glb gewandelt; dieses Werkzeug legt die zweite in die erste. Reines Python, keine Bibliothek: Puffer
hintereinander, alle Verweise (Puffersichten, Zugriffe, Netze, Stoffe, Bilder, Texturen, Knoten) verschoben, die
Wurzeln der zweiten Szene an die erste gehängt. Die Geometrie wird nicht angefasst.

**Die Bauten der zweiten Datei bleiben Bauten.** Ihre Namen bleiben, wie sie sind (die Maske erkennt Gelände und
Umfeld am Namensanfang — ein Vorsatz davor machte aus einem Gelände ein Bauteil); die Herkunft steht in
``extras.aiimaging_quelle = "umgebung"`` an jedem Knoten der zweiten Datei. Damit zählen sie für Bild und KI wie
jeder Bau (die Bauwerksmaske hält sie), und die Wahl des Hauptbaus im Umfeld bleibt beim Blickziel der Kamera
(``umfeld._hauptbau_am_ziel``) — die Umgebungsbauten sind dort Nachbarn wie die Platten des Situationsmodells.

    python tools/glb_zusammenfuehren.py <situation.glb> <umgebung.glb> <ziel.glb> [--ueberschreiben]

Ausgabe: ein Bericht als JSON — **nur Zahlen** (Knoten je Datei, Hüllboxen in glTF-Koordinaten, ihre Überdeckung
im Grundriss), nie ein Name aus der Datei und nie ein Pfad. Rückgabewert 0 (geschrieben), 2 (Aufruf falsch),
1 (eine Datei unlesbar).
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import glbbox  # noqa: E402

#: Die Marke an jedem Knoten der zweiten Datei.
QUELLE_FELD = "aiimaging_quelle"
QUELLE_UMGEBUNG = "umgebung"

_MAGIC, _JSON, _BIN = 0x46546C67, 0x4E4F534A, 0x004E4942

#: Welche Listen auf welche anderen verweisen (Feld → Liste, deren Index es trägt).
_VERWEISE = ("bufferViews", "accessors", "images", "samplers", "textures", "materials", "meshes", "nodes",
             "skins", "cameras")


class GlbFehler(ValueError):
    """Eine Datei ist keine lesbare glb (Satz ohne Pfad)."""


def lies_glb(daten: bytes) -> tuple[dict, bytes]:
    """``(json, bin)`` einer glb."""
    if len(daten) < 20:
        raise GlbFehler("Zu kurz für eine glb.")
    magic, version, _laenge = struct.unpack_from("<III", daten, 0)
    if magic != _MAGIC or version != 2:
        raise GlbFehler("Keine glb der Fassung 2.")
    pos, js, binaer = 12, None, b""
    while pos + 8 <= len(daten):
        n, art = struct.unpack_from("<II", daten, pos)
        stueck = daten[pos + 8:pos + 8 + n]
        if art == _JSON:
            js = json.loads(stueck.decode("utf-8"))
        elif art == _BIN:
            binaer = bytes(stueck)
        pos += 8 + n
    if js is None:
        raise GlbFehler("Die glb hat keinen JSON-Block.")
    return js, binaer


def schreibe_glb(js: dict, binaer: bytes) -> bytes:
    roh = json.dumps(js, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    roh += b" " * ((4 - len(roh) % 4) % 4)
    binaer = binaer + b"\x00" * ((4 - len(binaer) % 4) % 4)
    teile = struct.pack("<II", len(roh), _JSON) + roh
    if binaer:
        teile += struct.pack("<II", len(binaer), _BIN) + binaer
    return struct.pack("<III", _MAGIC, 2, 12 + len(teile)) + teile


def _verschiebe(obj, versatz: dict):
    """Alle Indexfelder in ``obj`` (rekursiv) um den Versatz ihrer Liste verschieben."""
    felder = {"bufferView": "bufferViews", "sampler": "samplers", "source": "images", "material": "materials",
              "mesh": "meshes", "skin": "skins", "camera": "cameras", "skeleton": "nodes", "node": "nodes"}
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if k in felder and isinstance(v, int) and not isinstance(v, bool):
                obj[k] = v + versatz[felder[k]]
            elif k == "children" and isinstance(v, list):
                obj[k] = [i + versatz["nodes"] for i in v]
            elif k == "joints" and isinstance(v, list):
                obj[k] = [i + versatz["nodes"] for i in v]
            elif k == "index" and isinstance(v, int) and not isinstance(v, bool):
                obj[k] = v + versatz["textures"]           # TextureInfo.index
            elif k in ("indices", "inverseBindMatrices", "input", "output") and isinstance(v, int):
                obj[k] = v + versatz["accessors"]
            elif k == "attributes" and isinstance(v, dict):
                obj[k] = {a: i + versatz["accessors"] for a, i in v.items()}
            elif k == "targets" and isinstance(v, list):
                obj[k] = [{a: i + versatz["accessors"] for a, i in t.items()} for t in v]
            else:
                _verschiebe(v, versatz)
    elif isinstance(obj, list):
        for v in obj:
            _verschiebe(v, versatz)


def fuehre_zusammen(a: bytes, b: bytes) -> tuple[bytes, dict]:
    """Die glb ``b`` in die glb ``a`` legen — ``(neue glb, bericht)``. ``a`` bleibt vorne, ihre Indizes unverändert."""
    ja, ba = lies_glb(a)
    jb, bb = lies_glb(b)
    if len(ja.get("buffers") or ()) > 1 or len(jb.get("buffers") or ()) > 1:
        raise GlbFehler("Mehr als ein Puffer — das kann dieses Werkzeug nicht (glb tragen einen).")
    if any("uri" in p for p in (ja.get("buffers") or []) + (jb.get("buffers") or [])):
        raise GlbFehler("Ein Puffer verweist auf eine Datei daneben — nur eingebettete glb.")
    ba = ba + b"\x00" * ((4 - len(ba) % 4) % 4)
    versatz = {k: len(ja.get(k) or ()) for k in _VERWEISE}
    jb = json.loads(json.dumps(jb))                          # tiefe Kopie
    for liste in _VERWEISE:
        for eintrag in jb.get(liste) or ():
            _verschiebe(eintrag, versatz)
    for sicht in jb.get("bufferViews") or ():
        sicht["buffer"] = 0
        sicht["byteOffset"] = int(sicht.get("byteOffset") or 0) + len(ba)
    for knoten in jb.get("nodes") or ():
        knoten.setdefault("extras", {})[QUELLE_FELD] = QUELLE_UMGEBUNG
    aus = json.loads(json.dumps(ja))
    for liste in _VERWEISE:
        if jb.get(liste):
            aus[liste] = list(aus.get(liste) or []) + list(jb[liste])
    aus["buffers"] = [{"byteLength": len(ba) + len(bb)}] if (ba or bb) else []
    # Die Wurzeln der aktiven Szene von b an die aktive Szene von a.
    sz_b = (jb.get("scenes") or [{}])[jb.get("scene", 0)] if jb.get("scenes") else {}
    wurzeln_b = [i + versatz["nodes"] for i in (sz_b.get("nodes") or ())] if sz_b else [
        i + versatz["nodes"] for i in range(len(jb.get("nodes") or ()))
        if i not in {c for n in jb.get("nodes") or () for c in (n.get("children") or ())}]
    if not aus.get("scenes"):
        aus["scenes"], aus["scene"] = [{"nodes": []}], 0
    nummer = aus.get("scene", 0)
    aus["scenes"][nummer]["nodes"] = list(aus["scenes"][nummer].get("nodes") or []) + wurzeln_b
    for feld in ("extensionsUsed", "extensionsRequired"):
        menge = list(dict.fromkeys((ja.get(feld) or []) + (jb.get(feld) or [])))
        if menge:
            aus[feld] = menge
    neu = schreibe_glb(aus, ba + bb)
    return neu, _bericht(ja, jb, aus)


def _huelle(js: dict):
    boxen = glbbox.knotenboxen(js)["knoten"]
    if not boxen:
        return None
    lo = [min(b[1][i] for b in boxen) for i in range(3)]
    hi = [max(b[2][i] for b in boxen) for i in range(3)]
    return [round(v, 2) for v in lo], [round(v, 2) for v in hi]


def _bericht(ja: dict, jb: dict, aus: dict) -> dict:
    """Nur Zahlen: Knoten und Hüllboxen (glTF, Y oben) je Datei und ihre Überdeckung im Grundriss (X, Z)."""
    ha, hb = _huelle(ja), _huelle(jb)
    ueber = None
    if ha and hb:
        breite = max(0.0, min(ha[1][0], hb[1][0]) - max(ha[0][0], hb[0][0]))
        tiefe = max(0.0, min(ha[1][2], hb[1][2]) - max(ha[0][2], hb[0][2]))
        flaeche_b = max((hb[1][0] - hb[0][0]) * (hb[1][2] - hb[0][2]), 1e-9)
        ueber = {"grundriss_m2": round(breite * tiefe, 1),
                 "anteil_der_umgebung": round(breite * tiefe / flaeche_b, 3)}
    return {"knoten": {"situation": len(ja.get("nodes") or ()), "umgebung": len(jb.get("nodes") or ()),
                       "zusammen": len(aus.get("nodes") or ())},
            "netze": {"situation": len(ja.get("meshes") or ()), "umgebung": len(jb.get("meshes") or ())},
            "huellbox_gltf": {"situation": ha, "umgebung": hb, "zusammen": _huelle(aus)},
            "ueberdeckung": ueber,
            "liegen_uebereinander": bool(ueber and ueber["grundriss_m2"] > 0.0),
            "hinweis": "Nur Zahlen, nie ein Name aus der Datei. Koordinaten in glTF (Y oben)."}


def situation_pruefen(situation, zusammen) -> dict:
    """Gilt das Modell nach dem Zusammenführen noch als **Situationsmodell** (``kameras.ist_situationsmodell``)?

    Die Regel verlangt eine flache Anlage (Höhe höchstens 15 % der Breite). Umgebungsbauten bis 86 m auf einer
    Anlage von rund 580 m liegen genau an dieser Grenze — fällt das Modell hinaus, rechnet die Kette es wie ein
    Haus (Kameras in Augenhöhe, Umfeld um «das Haus»). Das steht dann als Satz da, nicht still.
    """
    from aiimaging import kameras
    aus = {}
    for name, pfad in (("situation", situation), ("zusammen", zusammen)):
        box = glbbox.bauwerksbox(pfad).get("bbox_bauwerk")
        urteil = kameras.ist_situationsmodell(box) if box else {"ja": None, "flachheit": None}
        aus[name] = {"ja": urteil.get("ja"),
                     "flachheit": None if urteil.get("flachheit") is None else round(urteil["flachheit"], 3)}
    aus["satz"] = None
    if aus["situation"]["ja"] and not aus["zusammen"]["ja"]:
        aus["satz"] = ("ACHTUNG: Mit den Umgebungsbauten gilt das Modell nicht mehr als Situationsmodell (Höhe über "
                       f"{kameras.SITUATION_FLACHHEIT:.0%} der Breite) — die Kette rechnete es wie ein Haus. Nicht "
                       "verwenden, bevor das geklärt ist.")
    return aus


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("situation", help="die erste glb (bleibt vorne)")
    ap.add_argument("umgebung", help="die zweite glb (Umgebungsbauten)")
    ap.add_argument("ziel", help="die neue glb")
    ap.add_argument("--ueberschreiben", action="store_true")
    a = ap.parse_args(argv)
    pa, pb, ziel = Path(a.situation), Path(a.umgebung), Path(a.ziel)
    if any(p.suffix.lower() != ".glb" for p in (pa, pb, ziel)):
        print("Alle drei Dateien enden auf .glb.", file=sys.stderr)
        return 2
    if ziel.exists() and not a.ueberschreiben:
        print("Das Ziel gibt es schon; ersetzen nur mit --ueberschreiben.", file=sys.stderr)
        return 2
    if ziel.resolve() in (pa.resolve(), pb.resolve()):
        print("Das Ziel ist eine der Eingaben — die Eingaben bleiben unberührt.", file=sys.stderr)
        return 2
    try:
        neu, bericht = fuehre_zusammen(pa.read_bytes(), pb.read_bytes())
    except (OSError, GlbFehler, ValueError) as e:
        print(f"Nicht zusammengeführt: {type(e).__name__}"
              + (f" — {e}" if isinstance(e, GlbFehler) else ""), file=sys.stderr)
        return 1
    ziel.write_bytes(neu)
    bericht["situationsmodell"] = situation_pruefen(pa, ziel)
    print(json.dumps(bericht, indent=2, ensure_ascii=False))
    if bericht["situationsmodell"].get("satz"):
        print(bericht["situationsmodell"]["satz"], file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
