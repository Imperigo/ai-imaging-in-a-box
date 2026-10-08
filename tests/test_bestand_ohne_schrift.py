"""Bestandskörper bekommen den Bildauftrag «ohne Schrift» (Splat-Demo, 08.10.2026).

**Der Anlass:** Im Splat-Demolauf der HomeStation (Zentrale, 08.10.2026) übernahm KosmoOrbit
drei Quader aus dem Splat als Bestand. Der Prompt verlangte eine Fassade, und das Bildmodell
erfand an der Halle Fassade **und einen Fantasie-Schriftzug**. KosmoOrbit markiert Bestand
seither als glTF ``extras.role = "existing"`` am Knoten (Integrator, Runde 14).

Was hier festgehalten wird:

* Gelesen wird nur der JSON-Kopf der glb; ohne Bestand bleibt der Bildauftrag wörtlich.
* Mit Bestand hängt der Abholer :data:`kosmo_szene.BESTAND_ZUSATZ` an — positiv
  formuliert, weil der negative Prompt auf dem Vorgabe-Backbone nicht wirkt.
* Der Vermerk steht am Kameraurteil, der Satz in ``verdict.hinweise`` und sagt, dass die
  Wirkung ungemessen ist.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

from aiimaging import abholer, bruecke, kosmo_szene

import test_kettenlauf_26august as _kl
from test_sammelnachprobe_230 import KOSMO_AUTO_KAMERAS, _kette_gebaeude_6m, _kosmo_ordner, _vertrag


def _mit_rollen(glb: bytes, rollen: list) -> bytes:
    """Die glb mit ``extras.role`` je Knoten neu packen (``None`` = keine Rolle)."""
    laenge, _art = struct.unpack_from("<II", glb, 12)
    js = json.loads(glb[20:20 + laenge])
    js["nodes"] = []
    for i, rolle in enumerate(rollen):
        k = {"name": f"V{i + 1}", "mesh": 0}
        if rolle is not None:
            k["extras"] = {"role": rolle}
        js["nodes"].append(k)
    js["scenes"] = [{"nodes": list(range(len(rollen)))}]
    kopf = json.dumps(js).encode()
    kopf += b" " * (-len(kopf) % 4)
    rest = glb[20 + laenge:]
    gesamt = 12 + 8 + len(kopf) + len(rest)
    return (struct.pack("<III", 0x46546C67, 2, gesamt) + struct.pack("<II", len(kopf), 0x4E4F534A)
            + kopf + rest)


def test_ohne_rolle_gibt_es_keinen_bestand(tmp_path):
    pfad = tmp_path / "m.glb"
    pfad.write_bytes(_kl._minimale_glb())
    assert kosmo_szene.bestand_in_glb(pfad) is None


def test_die_rolle_existing_wird_gezaehlt(tmp_path):
    pfad = tmp_path / "m.glb"
    pfad.write_bytes(_mit_rollen(_kl._minimale_glb(), ["existing", None, "existing", "proposed"]))
    bestand = kosmo_szene.bestand_in_glb(pfad)
    assert bestand == {"n_bestand": 2, "n_knoten": 4, "namen": ["V1", "V3"]}


def test_eine_kaputte_datei_ist_kein_bestand(tmp_path):
    pfad = tmp_path / "m.glb"
    pfad.write_bytes(b"kein glb")
    assert kosmo_szene.bestand_in_glb(pfad) is None
    assert kosmo_szene.bestand_in_glb(tmp_path / "fehlt.glb") is None


def test_der_zusatz_ist_positiv_formuliert():
    auftrag = kosmo_szene.bildauftrag_bestand("house, plaster", {"n_bestand": 1, "n_knoten": 2})
    assert auftrag["gerechnet"] == "house, plaster, " + kosmo_szene.BESTAND_ZUSATZ
    assert "lettering" in kosmo_szene.BESTAND_ZUSATZ
    assert kosmo_szene.bildauftrag_bestand("house", None) is None


def _lauf(tmp_path, rollen):
    ordner = _kosmo_ordner(tmp_path, kameras=KOSMO_AUTO_KAMERAS[:1])
    (ordner / bruecke.DATEI_MODELL).write_bytes(_mit_rollen(_kl._minimale_glb(), rollen))
    protokoll, attrappen = _kette_gebaeude_6m()
    antwort = _kl._lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    return ordner, [a.prompt for a in protokoll["render"]]


def test_mit_bestand_bekommt_das_bild_den_zusatz_und_den_satz(tmp_path):
    ordner, prompts = _lauf(tmp_path, ["existing", None])
    assert prompts and all(p.endswith(kosmo_szene.BESTAND_ZUSATZ) for p in prompts)
    assert prompts[0].startswith("house, plaster, clear sky, ")
    kamera = abholer.lies_befund(ordner)["kameras"][0]
    assert kamera[kosmo_szene.URTEIL_BESTAND]["n_bestand"] == 1
    hinweise = _vertrag(ordner)["qa"]["verdict"]["hinweise"]
    assert any(h.startswith("BESTAND: 1 Körper als bestehend markiert") for h in hinweise)
    assert any("ungemessen" in h for h in hinweise)


def test_ohne_bestand_bleibt_der_bildauftrag_woertlich(tmp_path):
    ordner, prompts = _lauf(tmp_path, [None, "proposed"])
    assert prompts and all(p == "house, plaster, clear sky" for p in prompts)
    assert abholer.lies_befund(ordner)["kameras"][0].get(kosmo_szene.URTEIL_BESTAND) is None
    assert not any(h.startswith("BESTAND") for h in
                   _vertrag(ordner)["qa"]["verdict"].get("hinweise") or ())
