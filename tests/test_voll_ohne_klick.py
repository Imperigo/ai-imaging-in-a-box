"""Vollautomatik ohne Klick — die Grenzen setzt der Heim-PC durch (Owner-Entscheid 146, 24.10.2026).

Klickfrage über die Zentrale, Variante A «Alles ohne Klick, Grenzen bleiben»; Wortlaut des Owners:
«bitte behebe das kartenproblem und ständige "ich muss bestätigen" mit karten wenn vollautomatik
läuft». Am Mac (0.3.54, «Voll») brauchte ein Bild aus der Skizze vier Klicks.

Was hier festgehalten wird:

* **Die Mac-App sagt «Voll» an** (Kopf ``X-Visbox-Ohne-Klick: voll`` beim Anlegen). Der Heim-PC stellt
  den Auftrag dann selbst in die Reihe — ohne «Freigeben» — mit derselben Marke wie ein Klick und
  ``ohne_klick: True``.
* **Höchstens 5 Läufe ohne Klick in 60 Minuten, gleitend, über alle Geräte, hier gezählt.** Der
  sechste wartet auf «Freigeben», mit Zustand ``voll_grenze_erreicht`` und ``wieder_frei_ab``.
* **Nie ein Bildmodell mit Forschungs- oder offener Lizenz ohne Klick** (Qwen-Image 2.1).
* Ohne Kopf bleibt alles wie bisher; ein menschliches «Freigeben» zählt nicht zur Grenze.
* Die Seite kann den Kopf nicht setzen, und kein Weg der Seite gibt frei.

Regel 3: alles synthetisch.
"""
from __future__ import annotations

import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

import pytest

from aiimaging import backbone, bruecke, knotenweg

from test_knotenweg import SZENE, _Anfrage, _formular, _glb, server  # noqa: F401 — Fixture

WURZEL = Path(__file__).resolve().parents[1]
KERN = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern"
MAC = WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac"
WIRT = WURZEL / "kosmovis" / "apps" / "visbox-knoten" / "src"
T0 = 1_790_000_000.0


def _code(pfad: Path) -> str:
    return "\n".join(z for z in pfad.read_text(encoding="utf-8").splitlines()
                     if not z.lstrip().startswith(("//", "*", "/**")))


class _Uhr:
    def __init__(self, t: float = T0):
        self.t = t

    def __call__(self) -> float:
        return self.t


def _lege(ablage, uhr, *, ohne_klick=True, n=0, **vis):
    szene = dict(SZENE, vis={**SZENE["vis"], **vis})
    return knotenweg.lege_an(ablage, szene, b"glTF-bytes", "model.glb",
                             kennung=f"vis-{int(uhr())}-{n:06x}", ohne_klick=ohne_klick, _uhr=uhr)


# ---------------------------------------------------------------- 1 · die Grenze je Stunde


def test_sechs_laeufe_in_einer_stunde_der_sechste_wartet_mit_wieder_frei_ab(tmp_path):
    uhr = _Uhr()
    zettel = []
    for i in range(6):
        zettel.append(_lege(tmp_path, uhr, n=i))
        uhr.t += 60
    for z in zettel[:5]:
        assert z["status"] == bruecke.STATUS_QUEUED, z
        assert z[knotenweg.FELD_FREIGABE]["ohne_klick"] is True
        assert z[knotenweg.FELD_FREIGABE]["durch"] == knotenweg.FREIGABE_DURCH_VOLL
        assert bruecke.FELD_MELDUNG not in z
    sechster = zettel[5]
    assert sechster["status"] == bruecke.STATUS_AWAITING
    vermerk = sechster[knotenweg.FELD_VOLL]
    assert vermerk["zustand"] == knotenweg.ZUSTAND_GRENZE == "voll_grenze_erreicht"
    # GLEITEND: frei, sobald der erste aus den 60 Minuten faellt.
    assert vermerk["wieder_frei_ab"] == datetime.fromtimestamp(
        T0 + 3600, timezone.utc).isoformat(timespec="seconds")
    assert "Grenze erreicht: 5 Läufe ohne Klick" in sechster[bruecke.FELD_MELDUNG]
    assert knotenweg.FELD_FREIGABE not in sechster

    stand = knotenweg.voll_stand(tmp_path, _uhr=uhr)
    assert (stand["laeufe"], stand["frei"], stand["zustand"]) == (5, False, "voll_grenze_erreicht")
    # Eine Stunde nach dem ersten ist wieder einer frei — nicht erst zur vollen Uhrstunde.
    uhr.t = T0 + 3601
    assert knotenweg.voll_stand(tmp_path, _uhr=uhr)["frei"] is True
    assert _lege(tmp_path, uhr, n=99)["status"] == bruecke.STATUS_QUEUED


def test_der_wartende_sechste_geht_mit_einem_klick_und_zaehlt_nicht(tmp_path):
    uhr = _Uhr()
    for i in range(5):
        _lege(tmp_path, uhr, n=i)
    sechster = _lege(tmp_path, uhr, n=5)
    frei = knotenweg.freigeben(tmp_path, sechster["job_id"], sechster["approval_token"])
    assert frei["status"] == bruecke.STATUS_QUEUED
    assert "ohne_klick" not in frei[knotenweg.FELD_FREIGABE]
    assert knotenweg.voll_stand(tmp_path, _uhr=uhr)["laeufe"] == 5


def test_ohne_kopf_bleibt_alles_wie_bisher(tmp_path):
    uhr = _Uhr()
    z = _lege(tmp_path, uhr, ohne_klick=False)
    assert z["status"] == bruecke.STATUS_AWAITING
    assert knotenweg.FELD_VOLL not in z
    assert knotenweg.voll_stand(tmp_path, _uhr=uhr)["laeufe"] == 0


def test_zwei_geraete_zugleich_beim_fuenften_bekommt_nur_eines_ihn(tmp_path):
    uhr = _Uhr()
    for i in range(4):
        _lege(tmp_path, uhr, n=i)
    ergebnisse = []

    def bestelle(n):
        ergebnisse.append(_lege(tmp_path, uhr, n=n)["status"])

    faeden = [threading.Thread(target=bestelle, args=(10 + i,)) for i in range(4)]
    for f in faeden:
        f.start()
    for f in faeden:
        f.join()
    assert sorted(ergebnisse).count(bruecke.STATUS_QUEUED) == 1, ergebnisse
    assert knotenweg.voll_stand(tmp_path, _uhr=uhr)["laeufe"] == 5


# ---------------------------------------------------------------- 2 · die Lizenz


def test_qwen_image_21_wartet_auf_einen_klick_auch_wenn_die_stunde_frei_ist(tmp_path):
    uhr = _Uhr()
    # A0051b («Immer vom Render», Owner-Entscheid 31.10.2026): ohne Skizze bekommt qwen-image-2.1 den Beauty-Render
    # nicht als Start — die Bruecke nimmt die Bestellung gar nicht an (400), es zaehlt kein Lauf.
    with pytest.raises(knotenweg.KnotenwegError, match="MASSTREUE"):
        _lege(tmp_path, uhr, backbone="qwen-image-2.1")
    assert knotenweg.voll_stand(tmp_path, _uhr=uhr)["laeufe"] == 0


@pytest.mark.parametrize("vis, darf", [
    ({"backbone": "z-image-turbo"}, True),
    ({"backbone": None}, True),                       # Vorgabe des Vertrags
    ({"backbone": "flux2-klein"}, True),
    ({"backbone": "qwen"}, True),
    ({"backbone": "qwen-image-2.1"}, False),
    ({"backbone": "flux-krea"}, False),               # nicht kommerziell
    ({"backbone": "sdxl"}, False),
    ({"backbone": "gibts-nicht"}, False),
    ({"backbone": "qwen-image-2.1", "skip": True}, True),   # nur Blender: kein Bildmodell
    ({"backbone": "z-image-turbo", "research_only": True}, False),
])
def test_die_lizenz_grenze(vis, darf):
    assert (knotenweg.voll_lizenz_mangel({"vis": vis}) is None) is darf


def test_die_liste_folgt_dem_register_und_der_knotenansicht():
    frei = knotenweg.voll_bildmodelle()
    assert frei == ("flux2-klein", "qwen", "z-image-turbo")
    for kuerzel in frei:
        eintrag = backbone.hole(knotenweg.kosmo_szene.BACKBONE_VON_FREMD[kuerzel])
        assert not eintrag.nur_forschung and not eintrag.lizenz_offen
    ts = (WIRT / "voll-render.ts").read_text(encoding="utf-8")
    liste = re.search(r"VOLL_BILDMODELLE: readonly string\[\] = \[([^\]]*)\]", ts).group(1)
    assert tuple(sorted(re.findall(r"'([^']+)'", liste))) == frei
    assert f"VOLL_GRENZE_JE_STUNDE = {knotenweg.VOLL_GRENZE};" in ts
    assert f"public static let vollGrenze = {knotenweg.VOLL_GRENZE}" in _code(KERN / "Mcpkern.swift")
    assert knotenweg.VOLL_GRENZE == 5 and knotenweg.VOLL_FENSTER_S == 3600


# ---------------------------------------------------------------- 3 · über den Server


def _anlegen(server, ablage, koepfe=None, **vis):
    szene = dict(SZENE, vis={**SZENE["vis"], **vis})
    rumpf, typ = _formular({"scene": (None, json.dumps(szene).encode()),
                            "model": ("model.glb", b"glTF-attrappe")})
    a = _Anfrage(server, befehl="POST", weg="/bruecke/jobs", rumpf=rumpf, typ=typ, ablage=ablage)
    a.selbst.headers.update(koepfe or {})
    return a.stelle().json()


def test_der_server_liest_den_kopf_und_meldet_den_stand(server, tmp_path):
    ablage = tmp_path / "ablage"
    kopf = {knotenweg.KOPF_OHNE_KLICK: "voll"}
    assert _anlegen(server, ablage)["status"] == bruecke.STATUS_AWAITING, "ohne Kopf: Klick"
    assert _anlegen(server, ablage, {knotenweg.KOPF_OHNE_KLICK: "ja"})["status"] == bruecke.STATUS_AWAITING
    assert _anlegen(server, ablage, kopf)["status"] == bruecke.STATUS_QUEUED
    # A0051b («Immer vom Render», Owner-Entscheid 31.10.2026): ohne Skizze nimmt die Bruecke qwen-image-2.1 nicht an.
    assert "MASSTREUE" in json.dumps(_anlegen(server, ablage, kopf, backbone="qwen-image-2.1"),
                                     ensure_ascii=False)
    stand = _Anfrage(server, befehl="GET", weg="/bruecke/voll", ablage=ablage).stelle().json()
    assert stand["laeufe"] == 1 and stand["frei"] is True and stand["grenze"] == 5
    assert stand["satz"].startswith("Vollautomatik: 1 von 5 Läufen ohne Klick")


def test_der_abholer_erkennt_einen_lauf_ohne_klick_als_freigegeben(tmp_path):
    uhr = _Uhr()
    szene = dict(SZENE)
    z = knotenweg.lege_an(tmp_path, szene, _glb(tmp_path).read_bytes(), "model.glb",
                          kennung="vis-1790000000-00aa01", ohne_klick=True, _uhr=uhr)
    gelesen = bruecke.lies_auftrag(tmp_path / z["job_id"])
    assert gelesen["freigegeben"] is True
    assert knotenweg.FREIGABE_DURCH_VOLL in gelesen["freigabe_grund"]


# ---------------------------------------------------------------- 4 · die Verdrahtung am Mac


def test_nur_die_mac_app_setzt_den_kopf_und_nur_in_voll():
    wege = _code(KERN / "Knotenwege.swift")
    # Der Name aus der Marke (Regel des Gerüsts: «Visbox» steht nur in Marke.swift).
    assert 'public static let ohneKlickName = "X-\\(Marke.name)-Ohne-Klick"' in wege
    marke = (KERN / "Marke.swift").read_text(encoding="utf-8")
    assert re.search(r'static let name\s*=\s*"Visbox"', marke)
    assert knotenweg.KOPF_OHNE_KLICK == "X-Visbox-Ohne-Klick"
    assert f'public static let ohneKlickWert = "{knotenweg.WERT_OHNE_KLICK}"' in wege
    assert "guard modus == .voll" in wege and 'ohneSchraegstrich == "/bruecke/jobs"' in wege
    # Die Seite kann ihn nicht mitschicken: nur drei ihrer Koepfe gehen hinaus.
    assert 'koepfeHinaus: Set<String> = ["content-type", "accept", "x-kosmo-token"]' in wege
    quelle = _code(MAC / "Start" / "Knotenquelle.swift")
    assert "Knotenwege.ohneKlickKopf(methode:" in quelle and "Kizentrale.gemeinsam.modus" in quelle


def test_die_zentrale_fragt_den_heim_pc_vor_jedem_bild_in_voll():
    zentrale = _code(MAC / "Claude" / "Kizentrale.swift")
    assert "Kibruecke.brauchtVollLage(" in zentrale
    assert "Vollstand.text(await holeVollstand())" in zentrale
    assert '"voll": vollText' in zentrale
    assert "await heim(Macwerkzeuge.vollWeg)" in zentrale
    assert 'Heimweg(methode: "GET", pfad: "/bruecke/voll"' in _code(KERN / "Kibedienung.swift")


def test_visbox_status_und_anleitung_sagen_es_je_modus():
    kern = (KERN / "Mcpkern.swift").read_text(encoding="utf-8")
    assert "auch nicht in Voll" not in kern
    assert "gibt immer ein Mensch frei" not in kern
    for satz in ("Modus: Karte — jede Änderung wartet auf «Anwenden»",
                 "Modus: Coop — Änderungen laufen ohne Karte",
                 "Modus: Voll — Änderungen und Bilder (vis_render, vis_varianten, vis_grundlage)",
                 "In Voll rechnen sie sofort, ohne Karte und \"\n        + \"ohne Freigabe-Klick"):
        assert satz in kern, satz
    assert "if !lage.vollSatz.isEmpty { zeilen.append(lage.vollSatz) }" in kern


def test_kein_neuer_weg_der_seite_gibt_frei():
    for datei in ("voll-render.ts", "grundlage-werkzeug.ts"):
        code = _code(WIRT / datei)
        assert not re.search(r"approve|freigeben\(|render-freigeben|approval", code, re.I), datei
