#!/usr/bin/env python3
"""Welche Zahl folgt dem Augenurteil? — Auswertung für die Formprüfung (Sitzung 73 §17).

Liest Ergebnisdateien der HomeStation (``auftraege/ergebnisse/*.json``), deren Liste ``bilder``
je Bild ein ``augenetikett`` und Zahlen trägt, und sagt je Zahl:

* **AUC** — wie oft ein Bild, das das Auge «steht» nennt, eine höhere Zahl hat als eines, das
  es «steht nicht» nennt (0,5 = Münzwurf, 1,0 = trennt perfekt). Einmal ohne «unklar», einmal
  mit «unklar» als «steht nicht» gezählt.
* **AUC im Fall** — dasselbe, aber verglichen werden nur Bilder **desselben Falls** (Serie ×
  Körper × Blick × Rahmung). Das ist die Frage der Startwert-Auswahl, und sie ist frei vom
  gröbsten Störfaktor: Eine Zahl, die nur Frontal- von Schrägblicken oder Szenen- von
  Bauwerksrahmung trennt, trennt hier nichts. **Befund an 186/188/190 (30.09.):** Fast alle
  «steht nicht» stammen aus der Szenenrahmung — über alle Bilder gemessen, belohnt jede Zahl
  vor allem die Rahmung.
* **Kreuzpaare** — steht in der Ergebnisdatei eine Liste ``kreuzpaare`` (dasselbe Bild einmal
  gegen die eigene, einmal gegen eine fremde Soll-Karte), sagt ``kreuz`` je Zahl, bei welchem
  Anteil der Bilder die eigene Soll-Karte höher liegt als jede fremde. Das braucht kein Auge.
* **Treffer ohne eigenen Fall** — eine Schwelle wird an allen anderen Fällen (Serie × Körper ×
  Blick) gewählt und am ausgelassenen geprüft. Das ist die ehrliche Frage: Trägt eine Schwelle,
  die nicht an denselben Bildern gefunden wurde?

Je Körper getrennt, weil der Hochbau frontal der schwache Fall ist. Reine stdlib, kein Urteil —
die Entscheidungsregel steht im Auftrag, nicht hier.

Aufruf::

    python3 tools/formpruefung_auswertung.py auftraege/ergebnisse/auf-20260930-186.json ...
    python3 tools/formpruefung_auswertung.py --json DATEIEN...
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

#: Die Augenetiketten der Serien 186/188/190 und ihre Bedeutung. Was hier nicht steht, ist
#: ein Fehler — ein neues Wort heisst eine neue Frage, keine stille Einordnung.
ETIKETTEN = {
    "steht": True, "steht richtig": True,
    "steht nicht": False, "steht falsch": False,
    "unklar": None,
}

#: Felder einer Bildzeile, die keine Zahl zum Vergleichen sind.
KEINE_ZAHL = {"koerper", "blick", "startwert", "controlnet_staerke", "n_flaechen", "rahmung",
              "rahmung_gemeldet", "augenetikett", "halbsatz", "blind_id", "modus_gerechnet", "serie", "sekunden_gesamt",
              "sekunden_render", "bauwerk_anteil", "abhebung_schoenbild_gleiche_soll",
              "urteilt", "status", "grund"}


def auge(etikett: str) -> bool | None:
    try:
        return ETIKETTEN[etikett.strip().lower()]
    except KeyError:
        raise ValueError(f"Unbekanntes Augenetikett: {etikett!r}") from None


def kreuzpaare_aus(pfade) -> list[dict]:
    aus = []
    for pfad in pfade:
        aus += json.loads(Path(pfad).read_text(encoding="utf-8")).get("kreuzpaare") or []
    return aus


def zeilen_aus(pfade, *, rahmung: str | None = None) -> list[dict]:
    """Alle Bildzeilen, je mit ``serie`` (aus der Auftragsnummer) und ``auge``.

    ``rahmung`` behält nur Zeilen mit genau dieser Rahmung (Zeilen ohne Angabe fallen weg).
    """
    aus = []
    for pfad in pfade:
        daten = json.loads(Path(pfad).read_text(encoding="utf-8"))
        serie = str(daten.get("auftrag_id", Path(pfad).stem)).split()[0]
        for b in daten.get("bilder") or []:
            if "augenetikett" not in b:
                continue
            if rahmung is not None and b.get("rahmung") != rahmung:
                continue
            z = dict(b)
            z.setdefault("serie", serie)
            z["auge"] = auge(b["augenetikett"])
            aus.append(z)
    return aus


def masse_in(zeilen) -> list[str]:
    namen = set()
    for z in zeilen:
        for k, v in z.items():
            if k in KEINE_ZAHL or k == "auge" or isinstance(v, bool):
                continue
            if isinstance(v, (int, float)):
                namen.add(k)
    return sorted(namen)


def auc(positiv, negativ) -> float | None:
    """Mann-Whitney-AUC mit halben Punkten für Gleichstand; ``None`` ohne beide Seiten."""
    if not positiv or not negativ:
        return None
    s = 0.0
    for p in positiv:
        for n in negativ:
            s += 1.0 if p > n else (0.5 if p == n else 0.0)
    return s / (len(positiv) * len(negativ))


def _wert(z, mass):
    v = z.get(mass)
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) \
        and math.isfinite(v) else None


def _getrennt(zeilen, mass, unklar_als_falsch):
    pos, neg = [], []
    for z in zeilen:
        v = _wert(z, mass)
        if v is None:
            continue
        a = z["auge"]
        if a is None:
            if unklar_als_falsch:
                neg.append(v)
            continue
        (pos if a else neg).append(v)
    return pos, neg


def _fall(z):
    return (z["serie"], z["koerper"], z["blick"], z.get("rahmung"))


def _ausgewogen(zeilen, mass, schwelle):
    tp = fn = tn = fp = 0
    for z in zeilen:
        v = _wert(z, mass)
        if v is None or z["auge"] is None:
            continue
        ja = v >= schwelle
        if z["auge"]:
            tp, fn = tp + ja, fn + (not ja)
        else:
            tn, fp = tn + (not ja), fp + ja
    if tp + fn == 0 or tn + fp == 0:
        return None
    return 0.5 * (tp / (tp + fn) + tn / (tn + fp))


def beste_schwelle(zeilen, mass):
    werte = sorted({v for z in zeilen if (v := _wert(z, mass)) is not None})
    beste, wert = None, -1.0
    for s in werte:
        b = _ausgewogen(zeilen, mass, s)
        if b is not None and b > wert:
            beste, wert = s, b
    return beste


def auc_im_fall(zeilen, mass, unklar_als_falsch=False) -> float | None:
    """AUC nur über Paare aus demselben Fall — der Störfaktor Fall fällt heraus."""
    s = 0.0
    n = 0
    for fall in {_fall(z) for z in zeilen}:
        pos, neg = _getrennt([z for z in zeilen if _fall(z) == fall], mass, unklar_als_falsch)
        a = auc(pos, neg)
        if a is not None:
            s += a * len(pos) * len(neg)
            n += len(pos) * len(neg)
    return s / n if n else None


def kreuz(kreuzpaare, mass, zeilen=None) -> float | None:
    """Anteil der Bilder, deren eigene Soll-Karte höher liegt als jede fremde.

    Mit ``zeilen`` zählen nur Bilder, die das Auge «steht» nennt (über ``blind_id``) — bei
    einem Bild ohne Form muss die eigene Soll-Karte nicht gewinnen.
    """
    stehen = None if zeilen is None else {z.get("blind_id") for z in zeilen if z["auge"] is True}
    je_bild: dict = {}
    for k in kreuzpaare or ():
        if stehen is not None and k.get("bild") not in stehen:
            continue
        v = _wert(k, mass)
        if v is None:
            continue
        e = je_bild.setdefault(k["bild"], {"eigen": None, "fremd": []})
        if k.get("eigen"):
            e["eigen"] = v
        else:
            e["fremd"].append(v)
    gezaehlt = [e["eigen"] > max(e["fremd"]) for e in je_bild.values()
                if e["eigen"] is not None and e["fremd"]]
    return sum(gezaehlt) / len(gezaehlt) if gezaehlt else None


def ohne_eigenen_fall(zeilen, mass) -> float | None:
    """Treffer (Anteil richtig eingeordneter Bilder), Schwelle je Fall an den übrigen gewählt."""
    richtig = gesamt = 0
    for fall in sorted({_fall(z) for z in zeilen}):
        hier = [z for z in zeilen if _fall(z) == fall]
        rest = [z for z in zeilen if _fall(z) != fall]
        s = beste_schwelle(rest, mass)
        if s is None:
            continue
        for z in hier:
            v = _wert(z, mass)
            if v is None or z["auge"] is None:
                continue
            gesamt += 1
            richtig += (v >= s) == z["auge"]
    return richtig / gesamt if gesamt else None


def auswerten(zeilen, masse=None, kreuzpaare=None) -> dict:
    masse = masse or masse_in(zeilen)
    koerper = sorted({z["koerper"] for z in zeilen})
    aus = {"n_bilder": len(zeilen), "masse": {}}
    aus["augen"] = {
        k: {"steht": sum(1 for z in zeilen if z["koerper"] == k and z["auge"] is True),
            "steht_nicht": sum(1 for z in zeilen if z["koerper"] == k and z["auge"] is False),
            "unklar": sum(1 for z in zeilen if z["koerper"] == k and z["auge"] is None)}
        for k in koerper}
    for m in masse:
        eintrag = {"auc": auc(*_getrennt(zeilen, m, False)),
                   "auc_unklar_als_falsch": auc(*_getrennt(zeilen, m, True)),
                   "auc_im_fall": auc_im_fall(zeilen, m),
                   "auc_im_fall_unklar_als_falsch": auc_im_fall(zeilen, m, True),
                   "ohne_eigenen_fall": ohne_eigenen_fall(zeilen, m),
                   "kreuz": kreuz(kreuzpaare, m, zeilen),
                   "je_koerper": {}}
        for k in koerper:
            teil = [z for z in zeilen if z["koerper"] == k]
            eintrag["je_koerper"][k] = {
                "auc": auc(*_getrennt(teil, m, False)),
                "auc_unklar_als_falsch": auc(*_getrennt(teil, m, True)),
                "auc_im_fall": auc_im_fall(teil, m),
                "auc_im_fall_unklar_als_falsch": auc_im_fall(teil, m, True),
                "n": sum(1 for z in teil if _wert(z, m) is not None)}
        aus["masse"][m] = eintrag
    return aus


def _f(x):
    return "  –  " if x is None else f"{x:5.2f}"


def als_text(ergebnis) -> str:
    koerper = sorted(ergebnis["augen"])
    zeilen = [f"{ergebnis['n_bilder']} Bilder. Auge je Körper: " + "; ".join(
        f"{k} {a['steht']} steht / {a['steht_nicht']} nicht / {a['unklar']} unklar"
        for k, a in ergebnis["augen"].items())]
    kopf = "Mass".ljust(26) + "  AUC +unkl  Fall +unkl o.Fall kreuz " + " ".join(
        f"{k[:7]:>7} {'+unkl':>5} {'Fall':>5} {'+unkl':>5}" for k in koerper)
    zeilen += ["", kopf, "-" * len(kopf)]
    for m, e in sorted(ergebnis["masse"].items(),
                       key=lambda kv: -(kv[1]["auc"] if kv[1]["auc"] is not None else -1)):
        teil = " ".join(
            "  " + " ".join(_f(e["je_koerper"][k][f]) for f in (
                "auc", "auc_unklar_als_falsch", "auc_im_fall", "auc_im_fall_unklar_als_falsch"))
            for k in koerper)
        zeilen.append(f"{m[:26].ljust(26)}" + " ".join(_f(e[f]) for f in (
            "auc", "auc_unklar_als_falsch", "auc_im_fall", "auc_im_fall_unklar_als_falsch",
            "ohne_eigenen_fall", "kreuz")) + teil)
    return "\n".join(zeilen)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("dateien", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--rahmung", choices=("bauwerk", "szene"),
                    help="nur Bilder mit dieser Rahmung (Zeilen ohne Angabe fallen weg)")
    a = ap.parse_args(argv)
    ergebnis = auswerten(zeilen_aus(a.dateien, rahmung=a.rahmung),
                         kreuzpaare=kreuzpaare_aus(a.dateien))
    print(json.dumps(ergebnis, ensure_ascii=False, indent=1) if a.json else als_text(ergebnis))
    return 0


if __name__ == "__main__":
    sys.exit(main())
