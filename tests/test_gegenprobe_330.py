"""Folgen der Gegenprobe 330 (Demo-Kette auf 0.3.34, 22.10.2026, Protokoll 74 §233).

Die Logik prüft ``vitest`` (``kosmovis/apps/visbox-knoten/test/varianten.test.tsx``, drüben
``kv-varianten-dauer.test.ts``). Hier bewacht:

* B2 — der Varianten-Knoten schätzte «ungefähr 3 min 2 s» für zwei Bilder, die auf der Grundlage des
  Render-Knotens in 92 s fertig waren. Die Schätzung fragt jetzt dieselbe Regel wie die Bestellung
  (``grundlageDerVariante``), und es gibt diese Regel nur einmal.
* Die Zahlen der Schätzung tragen ihre Herkunft: 47 s je Bild auf der Grundlage (330: 92 s für zwei),
  ohne Grundlage Cycles + 47 s + 9 s (328: 194 s, 330: 205 s für zwei).
* Variante B rechnet weiter mit drei Startwerten (geprüft, nicht gebaut — Begründung im Protokoll).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
VIS = WURZEL / "kosmovis" / "apps" / "kosmo-orbit" / "src" / "modules" / "vis"
ERGEBNIS = WURZEL / "auftraege" / "ergebnisse" / "auf-20261022-330.json"


def _lies(pfad: Path) -> str:
    return pfad.read_text(encoding="utf-8")


def _cycles(abtastungen: int, breite: int, hoehe: int) -> int:
    # Dieselbe Gerade wie `zeitschaetzungSekunden` (vis-jobs.ts): 83 s bei 128, 775 s bei 2048 auf 4000 × 2667.
    je = (775 - 83) / (2048 - 128)
    return round(83 - 128 * je + je * abtastungen * (breite * hoehe) / (4000 * 2667))


def test_b2_eine_regel_fuer_versand_und_schaetzung():
    jobs = _lies(VIS / "vis-jobs.ts")
    assert jobs.count("export function grundlageDerVariante(") == 1
    assert "export function varianteAufGrundlage(" in jobs
    # Der Versand ruft sie; die alte, eigene Bedingung im Versand gibt es nicht mehr.
    rumpf = jobs[jobs.index("export function sendeGraphRenderAuftrag("):]
    # Geraeteprobe R56 (Protokoll 74 §264, bewusst umgestellt): der Stand der Grundlage kommt aus EINER Regel
    # (`standDerGrundlageFuerVariante`, Teilmenge der Kameras), die Versand und Schaetzung beide fragen.
    assert "grundlageDerVariante(node?.params, standGrundlage" in rumpf
    assert jobs.count("standDerGrundlageFuerVariante(") == 3
    assert "!variante.entwurf && opts?.grundlage === undefined && !ohneKi" not in rumpf
    varianten = _lies(VIS / "varianten.ts")
    assert "varianteAufGrundlage(doc, mit.graph, render.id" in varianten


def test_b2_die_zahlen_und_ihre_herkunft():
    varianten = _lies(VIS / "varianten.ts")
    ki = int(re.search(r"export const KI_SEKUNDEN_JE_BILD_ANNAHME = (\d+);", varianten).group(1))
    zuschlag = int(re.search(r"export const STARTWERTAUSWAHL_SEKUNDEN_JE_BILD_ANNAHME = (\d+);", varianten).group(1))
    e = json.loads(_lies(ERGEBNIS))
    a = e["schritte"]["S6_variante_voll_a"]
    b = e["schritte"]["S7_variante_voll_b"]
    # Auf der Grundlage: zwei Bilder, ein Startwert — die Schaetzung liegt hoechstens 5 s neben der Messung.
    assert a["grundlage"]["wiederverwendet"] is True
    assert abs(2 * ki - a["dauer_s"]) <= 5
    # Ohne Grundlage (Material B): Cycles + KI + Zuschlag, zwischen 328 (194 s) und 330 (205 s).
    assert b["grundlage"]["wiederverwendet"] is False
    ohne = 2 * (_cycles(128, 1600, 1000) + ki + zuschlag)
    assert b["dauer_328_s"] <= ohne <= b["dauer_s"]
    # Der alte Wert stand im Ergebnis wortwoertlich am Knoten.
    assert "ungefähr 3 min 2 s" in e["schritte"]["S3_kamera_stimmung"]["varianten_knoten_woertlich"]
    assert 2 * (_cycles(128, 1600, 1000) + ki) == 182


def test_der_satz_am_tooltip_sagt_wann_die_47_s_allein_gelten():
    satz = re.search(r"export const DAUER_ANNAHME_SATZ =\s*'([^']+)'", _lies(VIS / "varianten.ts")).group(1)
    assert "Liegt am Render-Knoten die Grundlage" in satz
    assert "drei Startwerten" in satz


def test_variante_b_rechnet_weiter_mit_drei_startwerten():
    # Geprueft, nicht gebaut (§233): ohne passende Grundlage geht kein `vis.seed` mit — der Heim-PC waehlt
    # aus drei Startwerten den mit der besten Umrisstreue.
    jobs = _lies(VIS / "vis-jobs.ts")
    regel = jobs[jobs.index("export function grundlageDerVariante("):jobs.index("export function varianteAufGrundlage(")]
    assert "return g && g.stand === standJetzt ? g : null;" in regel
