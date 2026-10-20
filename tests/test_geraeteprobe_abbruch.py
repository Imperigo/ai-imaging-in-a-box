"""Die Geräteprobe der HomeStation vom 20.10.2026 — fünf Befunde am Abbruch und an der Freigabe.

Gerechnet auf ``main`` mit zwei Kameras, 768 x 512, 32 Samples, z-image-turbo:

1. **Das Teilbild trug den falschen Namen.** ``<zweite Kamera>__teilbild.png`` war
   bytegleich mit dem KI-Bild der ersten — ``_Fortschritt`` führte EINE Kamera für zwei
   Bilder. Jetzt je Bild seine Kamera.
2. **Der Abbruchsatz nannte die falsche Phase** («Phase blender», obwohl Blender fertig war
   und das Bildmodell anstand). Jetzt: «vor dem Bildmodell».
3. **Der Fortschritt blieb nach dem Abbruch stehen** (``blender``, 0.6), als liefe der
   Auftrag noch. Jetzt Phase ``abgebrochen`` mit dem erreichten Anteil.
4. **``/approve`` vermerkte immer «Klick in der Knotenansicht»**, auch über die API. Jetzt
   ehrlich: das Gerät, wenn der Kopf es sagt, sonst neutral.
5. **Abbruch und Fortschritt schrieben den Laufzettel ohne Sperre** — ein ``running`` konnte
   ein ``cancelled`` überschreiben. Jetzt Sperre und Wache.

Regel 3: alles synthetisch.
"""
from __future__ import annotations

import contextlib
import json
import threading
import time

from aiimaging import abholer, bruecke, knotenweg

from test_fortschritt_lauf import JOB, _bricht_ab_bei, _lauf, _zettel
from test_kettenlauf_26august import _auftragsordner
from test_knotenweg import SZENE, _Anfrage, _formular, server  # noqa: F401 — Fixture
from test_vorschau_guete import _attrappen


# ======================================================================================
# 1–3 · Teilbild, Satz und Endstand eines Abbruchs
# ======================================================================================

def _abbruch_nach_blender_der_zweiten_kamera(tmp_path):
    ordner = _auftragsordner(tmp_path)
    protokoll, attrappen = _attrappen(tmp_path)
    attrappen = _bricht_ab_bei(attrappen, "_multipass", ordner, nach=2)
    return ordner, protokoll, _lauf(tmp_path, ordner, attrappen)


def test_das_teilbild_traegt_die_kamera_seines_bilds(tmp_path):
    ordner, protokoll, antwort = _abbruch_nach_blender_der_zweiten_kamera(tmp_path)

    assert antwort["tat"] == abholer.TAT_ABGEBROCHEN, antwort["grund"]
    assert len(protokoll["render"]) == 1, "nur die erste Kamera hat ein KI-Bild"
    # Das KI-Bild der ersten Kamera ist das Teilbild — und es heisst nach IHR.
    assert antwort["teilbild"] == "s__teilbild.png"
    ki_bild = protokoll["render"][0].ausgabe_png
    # Seit auf-20261020-292 (B5) rechnet das Bildmodell 200 x 125 gerastert in `_ki_raster/`;
    # das Teilbild ist das auf die bestellte Groesse zurueckgebrachte Bild daneben.
    from pathlib import Path
    if abholer.KI_RASTER_ORDNER in Path(ki_bild).parts:
        ki_bild = Path(ki_bild).parent.parent / Path(ki_bild).name
    assert (ordner / "s__teilbild.png").read_bytes() == open(ki_bild, "rb").read()
    assert not (ordner / "sSE__teilbild.png").exists()


def test_der_abbruchsatz_nennt_den_naechsten_schritt(tmp_path):
    _ordner, _protokoll, antwort = _abbruch_nach_blender_der_zweiten_kamera(tmp_path)

    assert "vor dem Bildmodell" in antwort["grund"]
    assert "Kamera 2 von 3" in antwort["grund"]
    assert "Phase blender" not in antwort["grund"]


def test_nach_dem_abbruch_steht_der_endstand_am_auftrag(tmp_path):
    ordner, _protokoll, _antwort = _abbruch_nach_blender_der_zweiten_kamera(tmp_path)

    zettel = _zettel(ordner)
    assert zettel["status"] == bruecke.STATUS_CANCELLED
    fortschritt = zettel["progress"]
    assert fortschritt["phase"] == abholer.PHASE_ABGEBROCHEN
    assert 0.0 < fortschritt["pct"] < 1.0, "der erreichte Anteil bleibt"
    assert fortschritt["rest_s"] is None, "abgebrochen schaetzt keine Restzeit"
    bruecke.pruefe_fortschritt(fortschritt)


def test_ein_abbruch_nach_dem_bildmodell_sagt_vor_der_pruefung(tmp_path):
    ordner = _auftragsordner(tmp_path)
    _protokoll, attrappen = _attrappen(tmp_path)
    attrappen = _bricht_ab_bei(attrappen, "_rendere", ordner, nach=1)

    antwort = _lauf(tmp_path, ordner, attrappen)

    assert "Kamera 1 von 3, vor der Pruefung" in antwort["grund"]
    assert antwort["teilbild"] == "s__teilbild.png"


def test_auch_der_spaete_abbruch_schreibt_den_endstand(tmp_path):
    """Der Abbruch nach dem letzten Blick des Verarbeiters: Bis heute stand danach
    «pruefung, 1.0» am Auftrag — wie fertig."""
    ordner = _auftragsordner(tmp_path)
    bild = tmp_path / "aus" / "s" / "bild.png"
    bild.parent.mkdir(parents=True)
    bild.write_bytes(b"\x89PNG-attrappe")

    def verarbeite(auftrag):
        bruecke.setze_fortschritt(ordner, {"phase": "pruefung", "pct": 1.0, "rest_s": 0})
        knotenweg.abbrechen(tmp_path, JOB)
        return {"bilder": [str(bild)]}

    antwort = abholer.hole_einen(ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite)

    assert antwort["tat"] == abholer.TAT_ABGEBROCHEN
    assert _zettel(ordner)["progress"] == {"phase": "abgebrochen", "pct": 1.0, "rest_s": None}


def test_ein_abbruch_vor_der_zweiten_kamera_sagt_vor_blender(tmp_path):
    ordner = _auftragsordner(tmp_path)
    _protokoll, attrappen = _attrappen(tmp_path)
    echt = attrappen["_qa"]
    zaehler = {"n": 0}

    def qa_und_abbruch(*a, **k):
        zaehler["n"] += 1
        erg = echt(*a, **k)
        if zaehler["n"] == 1:
            # Nach der Messung der ersten Kamera; der naechste Blick, der zaehlt, ist am
            # Beginn der zweiten — vor ihrem Blender-Lauf.
            knotenweg.abbrechen(ordner.parent, ordner.name)
        return erg

    antwort = _lauf(tmp_path, ordner, dict(attrappen, _qa=qa_und_abbruch),
                    _abgebrochen=_erst_ab_kamera_zwei(ordner))
    assert "Kamera 2 von 3, vor Blender" in antwort["grund"], antwort["grund"]


def _erst_ab_kamera_zwei(ordner):
    """Ein Blick auf den Abbruch, der die Pruefungsphase der ersten Kamera uebergeht."""
    blicke = {"n": 0}

    def abgebrochen(o):
        blicke["n"] += 1
        # Blick 1: Kamera 1 Beginn; 2: Bildmodell; 3: Pruefung — erst ab dem vierten zaehlt.
        return blicke["n"] >= 4 and abholer.steht_abgebrochen(o)

    return abgebrochen


# ======================================================================================
# 4 · Die Herkunft einer Freigabe
# ======================================================================================

def _wartender_auftrag(server, ablage):
    rumpf, typ = _formular({"scene": (None, json.dumps(SZENE).encode()),
                            "model": ("model.glb", b"glTF-attrappe")})
    return _Anfrage(server, befehl="POST", weg="/bruecke/jobs", rumpf=rumpf, typ=typ,
                    ablage=ablage).stelle().json()


def _freigeben(server, ablage, zettel, koepfe=None):
    anfrage = _Anfrage(server, befehl="POST",
                       weg=f"/bruecke/jobs/{zettel['job_id']}/approve",
                       rumpf=json.dumps({"approval_token": zettel["approval_token"]}).encode(),
                       ablage=ablage)
    anfrage.selbst.headers.update(koepfe or {})
    return anfrage.stelle().json()


def test_ohne_geraetekopf_ist_die_freigabe_neutral(server, tmp_path):
    zettel = _wartender_auftrag(server, tmp_path / "ablage")
    frei = _freigeben(server, tmp_path / "ablage", zettel)
    assert frei[knotenweg.FELD_FREIGABE]["durch"] == knotenweg.FREIGABE_DURCH_NEUTRAL
    assert "Klick" not in json.dumps(frei[knotenweg.FELD_FREIGABE], ensure_ascii=False)


def test_mit_geraetekopf_steht_das_geraet_in_der_marke(server, tmp_path):
    zettel = _wartender_auftrag(server, tmp_path / "ablage")
    frei = _freigeben(server, tmp_path / "ablage", zettel,
                      {"X-Geraet": "ipad", "X-Geraet-Weg": "mac"})
    durch = frei[knotenweg.FELD_FREIGABE]["durch"]
    assert "ipad" in durch and "mac" in durch


def test_die_bibliothek_nimmt_eine_genannte_herkunft(tmp_path):
    ablage = tmp_path / "ablage"
    ordner = _auftragsordner(ablage)
    zettel = _zettel(ordner)
    zettel["status"] = bruecke.STATUS_AWAITING
    (ordner / bruecke.DATEI_LAUFZETTEL).write_text(json.dumps(zettel), encoding="utf-8")
    frei = knotenweg.freigeben(ablage, JOB, zettel["approval_token"], durch="Probe")
    assert frei[knotenweg.FELD_FREIGABE]["durch"] == "Probe"


# ======================================================================================
# 5 · Ein Abbruch geht nicht zwischen zwei Schreibern verloren
# ======================================================================================

def _laufender_auftrag(tmp_path):
    ordner = _auftragsordner(tmp_path)
    bruecke.setze_status(ordner, bruecke.STATUS_RUNNING)
    return ordner


def test_die_wache_behaelt_ein_dazwischen_gesetztes_cancelled(tmp_path, monkeypatch):
    """Ohne Sperre (wie auf einem System ohne ``flock``): Der Abbruch faellt GENAU zwischen
    Lesen und Zurueckschreiben des Fortschritts — die Wache behaelt ihn."""
    ordner = _laufender_auftrag(tmp_path)
    monkeypatch.setattr(bruecke, "laufzettel_sperre", lambda ziel: contextlib.nullcontext())
    echt = bruecke._lies_json
    einmal = {"n": 0}

    def lies_und_brich_ab(pfad, was):
        satz = echt(pfad, was)
        if einmal["n"] == 0:
            einmal["n"] = 1
            knotenweg.abbrechen(tmp_path, JOB)    # schreibt cancelled, nachdem gelesen ist
        return satz

    monkeypatch.setattr(bruecke, "_lies_json", lies_und_brich_ab)
    bruecke.setze_fortschritt(ordner, {"phase": "blender", "pct": 0.6})

    zettel = _zettel(ordner)
    assert zettel["status"] == bruecke.STATUS_CANCELLED, "running ueberschrieb den Abbruch"
    assert zettel[bruecke.FELD_MELDUNG] == "Vom Nutzer abgebrochen."
    assert zettel["progress"]["pct"] == 0.6


def test_die_sperre_ordnet_abbruch_und_fortschritt_hintereinander(tmp_path, monkeypatch):
    """Mit Sperre, zwei Faeden: Der Fortschritt liest und wartet; der Abbruch kommt waehrend
    dessen — und muss warten, bis der Fortschritt geschrieben hat."""
    ordner = _laufender_auftrag(tmp_path)
    echt = bruecke._lies_json
    gelesen = threading.Event()

    def langsam(pfad, was):
        satz = echt(pfad, was)
        if threading.current_thread().name == "fortschritt":
            gelesen.set()
            time.sleep(0.3)
        return satz

    monkeypatch.setattr(bruecke, "_lies_json", langsam)
    faden = threading.Thread(
        name="fortschritt",
        target=lambda: bruecke.setze_fortschritt(ordner, {"phase": "blender", "pct": 0.6}))
    faden.start()
    assert gelesen.wait(5)
    beginn = time.monotonic()
    knotenweg.abbrechen(tmp_path, JOB)
    gewartet = time.monotonic() - beginn
    faden.join(5)

    zettel = _zettel(ordner)
    assert zettel["status"] == bruecke.STATUS_CANCELLED
    assert zettel["progress"]["pct"] == 0.6
    assert gewartet > 0.1, "der Abbruch hat auf die Sperre gewartet"


def test_running_ueber_cancelled_bleibt_cancelled(tmp_path):
    ordner = _auftragsordner(tmp_path)
    knotenweg.abbrechen(tmp_path, JOB)
    bruecke.setze_status(ordner, bruecke.STATUS_RUNNING)
    assert _zettel(ordner)["status"] == bruecke.STATUS_CANCELLED
