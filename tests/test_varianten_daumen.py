"""Varianten-Daumen (Blatt 36, 21.10.2026): kommen die Bilder der Varianten über den Wirt an?

Der Varianten-Knoten der Knotenansicht zeigt je Variante ein Daumenbild. Er holt es über denselben Weg wie
das Bild am Render-Knoten und das Raster im Bildvergleich: ``/bruecke/jobs/<kennung>`` für das Ergebnis,
``/bruecke/jobs/<kennung>/artifacts/<name>`` für jedes Bild (``BridgeBild`` → ``bildBlob``). Hier wird der
Weg so gefahren, wie eine Varianten-Bestellung ihn braucht: ein Auftrag mit mehreren Standpunkten, ein Bild
je Kamera, dazu die Felder, die am Daumen eine Marke setzen (``guete``, ``engine_license_open``).

Dazu eine Wache für den Bau: Bis zum 21.10.2026 fehlte in ``vis-visual.css`` eine schliessende Klammer.
Alle Stilregeln danach — auch die der Daumen — wurden im Browser zu Unterregeln einer fremden Regel und
griffen nicht; gesehen hat es keine Probe, weil jede nur ihren Baustein prüfte. Die Wache zählt die Klammern
des gebauten Stilblatts und verlangt, dass die Regeln der Daumen auf oberster Ebene stehen.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote

from aiimaging import bruecke

from test_knotenweg import SZENE, _Anfrage, _formular, server  # noqa: F401  (Fixture)

WURZEL = Path(__file__).resolve().parents[1]
DIST = WURZEL / "kosmovis" / "apps" / "visbox-knoten" / "dist"
QUELLE = WURZEL / "kosmovis" / "apps" / "kosmo-orbit" / "src" / "modules" / "vis"

#: Drei Standpunkte, eine Stimmung, ein Entwurf — die Vorgabe des Varianten-Knotens (Entscheid 92a).
KAMERAS = ["Süd", "Südost", "Nordwest"]


def test_drei_standpunkte_drei_bilder_ueber_den_wirt(server, tmp_path):  # noqa: F811
    ablage = tmp_path / "ablage"
    szene = {**SZENE, "cameras": [{"name": k} for k in KAMERAS],
             "style": {"mode": "none", "prompt": "Abendstimmung"}}
    rumpf, typ = _formular({"scene": (None, json.dumps(szene).encode()),
                            "model": ("model.glb", b"glTF-bytes")})
    a = _Anfrage(server, befehl="POST", weg="/bruecke/jobs", rumpf=rumpf, typ=typ, ablage=ablage).stelle()
    assert a.codes == [200], a.selbst.wfile.getvalue()
    zettel = a.json()
    kennung = zettel["job_id"]
    frei = _Anfrage(server, befehl="POST", weg=f"/bruecke/jobs/{kennung}/approve",
                    rumpf=json.dumps({"approval_token": zettel["approval_token"]}).encode(),
                    ablage=ablage).stelle()
    assert frei.codes == [200]

    # Die HomeStation legt je Kamera ein Bild und das Ergebnis ab (erfundene Bytes, Regel 3).
    ordner = ablage / kennung
    namen = [f"{k}.png" for k in KAMERAS]
    for i, n in enumerate(namen):
        (ordner / n).write_bytes(b"\x89PNG-daumen-" + bytes([i]))
    (ordner / bruecke.DATEI_ERGEBNIS).write_text(json.dumps({
        "images": namen,
        "guete": "vorschau",
        "engine_used": "testmodell", "engine_license": "erfunden", "engine_license_open": True,
        "qa_je_kamera": [{"kamera": k, "lieferstatus": "geliefert", "bilder_soll": 1, "bilder_ist": 1}
                         for k in KAMERAS],
    }), encoding="utf-8")

    lauf = _Anfrage(server, befehl="GET", weg=f"/bruecke/jobs/{kennung}", ablage=ablage).stelle()
    assert lauf.codes == [200]
    ergebnis = lauf.json()["result"]
    # Was der Daumen liest: die Bilder in der Reihenfolge der Kameras, die Güte und die offene Lizenz.
    assert ergebnis["images"] == namen
    assert ergebnis["guete"] == "vorschau"
    assert ergebnis["engine_license_open"] is True
    assert [k["kamera"] for k in ergebnis["qa_je_kamera"]] == KAMERAS

    for i, n in enumerate(namen):
        bild = _Anfrage(server, befehl="GET", weg=f"/bruecke/jobs/{kennung}/artifacts/{quote(n)}",
                        ablage=ablage).stelle()
        assert bild.codes == [200], n
        assert bild.selbst.wfile.getvalue() == b"\x89PNG-daumen-" + bytes([i])


def _tiefe_vor(text: str, stelle: int) -> int:
    ohne = re.sub(r"/\*.*?\*/", lambda m: " " * len(m.group(0)), text[:stelle], flags=re.S)
    return ohne.count("{") - ohne.count("}")


def test_der_bau_traegt_die_daumen_und_ihre_regeln_greifen():
    # Was die Seite wirklich laedt, steht in `index.html` (neben dem Hauptskript liegen weitere Teilstuecke).
    seite = (DIST / "index.html").read_text(encoding="utf-8")
    stile = re.findall(r'assets/(index-[^"]+\.css)', seite)
    skripte = re.findall(r'assets/(index-[^"]+\.js)', seite)
    assert len(stile) == 1 and len(skripte) == 1, "genau ein Stilblatt und ein Hauptskript in der Seite"
    stile = [DIST / "assets" / stile[0]]
    skripte = [DIST / "assets" / skripte[0]]
    css = stile[0].read_text(encoding="utf-8")
    js = skripte[0].read_text(encoding="utf-8")
    assert "varianten-daumen-bild" in js, "der Bau traegt die Bildzeile des Varianten-Knotens"
    ohne = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    assert ohne.count("{") == ohne.count("}"), "das gebaute Stilblatt hat offene Klammern"
    for regel in (".vis-vdaumen{", ".vis-vdaumen-bild{", ".vis-guete-marke{", ".vis-node-grundlage{"):
        stelle = css.find(regel)
        if stelle < 0:
            # Nachzug Int 1 R63 (Protokoll 74 §279): eine Regel kann eine Gruppe anführen
            # (`.vis-guete-marke,.vis-modus-marke{` — Güte- und Modus-Marke teilen die Form).
            stelle = css.find(regel[:-1] + ",")
        assert stelle >= 0, regel
        assert _tiefe_vor(css, stelle) == 0, f"{regel} steht verschachtelt und greift nicht"


def test_die_quelle_des_stilblatts_ist_geschlossen():
    """Dieselbe Zählung an jeder Stildatei der Kopie — der Fehler entsteht in der Quelle, nicht im Bau."""
    for datei in sorted(QUELLE.glob("*.css")):
        ohne = re.sub(r"/\*.*?\*/", "", datei.read_text(encoding="utf-8"), flags=re.S)
        tiefe = 0
        for zeichen in ohne:
            tiefe += (zeichen == "{") - (zeichen == "}")
            assert tiefe >= 0, datei.name
        assert tiefe == 0, f"{datei.name}: {tiefe} Klammer(n) offen"
