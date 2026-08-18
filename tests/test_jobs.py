"""Das Freigabe-Gate — geprüft ohne GPU, ohne Blender, ohne Netz.

``jobs.py`` trägt eine einzige Zusage, und die ist der Grund für dieses Modul:
**der Status folgt allein dem Freigabe-Token.** Ein Sprachmodell soll Aufträge
einstellen können, ohne die Grafikkarte belegen zu können (siehe
``docs/EINBINDUNG_KOSMOORBIT_2026-08-14.md`` §3.3 — der Ausführungspfad des Cockpits ist
read-only und fail-closed).

Eine solche Zusage sieht man dem Code nicht an; sie hält nur, solange sie geprüft wird.
Darum stehen hier drei Sorten Test:

1. **Das Gate** — kein Weg nach ``queued`` ausser über ein gültiges Token, und zwar
   weder über ``baue_job`` noch über ``setze_status``.
2. **Der Statusgraph** — jeder erlaubte Übergang einmal, dazu die verbotenen.
3. **Die Ablage** — Pfad-Trickserei und Atomizität. Ein halb geschriebener Auftrag, den
   ein Scheduler später für gültig hält, wäre ein GPU-Lauf auf Datenmüll.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from aiimaging import jobs
from aiimaging.jobs import (
    ALLE_STATUS,
    JOB_ID_MUSTER,
    STATUS_AWAITING,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_ERROR,
    STATUS_QUEUED,
    STATUS_RUNNING,
    TOKEN_PRAEFIX,
    JobError,
    UebergangError,
    baue_job,
    freigeben,
    ist_gueltiges_token,
    lies_job,
    liste_jobs,
    neue_job_id,
    schreibe_job,
    setze_status,
)

#: Ein Token, wie es der Mensch am Cockpit erteilt.
GUELTIG = TOKEN_PRAEFIX + "nutzer-hat-bestaetigt"

#: Synthetische Auftragsparameter (Regel 3: keine echten Projektdaten, nichts, was nach
#: Büro, Kunde oder Projekt klingt).
PARAMS = {"glb_path": "/synthetisch/wuerfel.glb", "up_axis": "Y", "aufloesung": 512}


def _job(verzeichnis, job_id="vis-20260818120000-abc123", *, token=None, **rest) -> dict:
    """Auftrag bauen und ablegen — die Vorbedingung fast jedes Tests hier."""
    satz = baue_job(job_id=job_id, art="depth", params=PARAMS, approval_token=token, **rest)
    schreibe_job(satz, verzeichnis)
    return satz


def _bringe_auf(verzeichnis, ziel: str, job_id="vis-20260818120000-abc123") -> dict:
    """Auftrag auf einen Ausgangsstatus bringen — nur über erlaubte Wege.

    Bewusst kein Schreiben des Status von Hand: Ein Test, der sich seinen Ausgangszustand
    an der Ablage vorbei baut, prüft am Ende einen Zustand, den es im Betrieb nicht gibt.
    """
    _job(verzeichnis, job_id)
    if ziel == STATUS_AWAITING:
        return lies_job(job_id, verzeichnis)
    if ziel == STATUS_CANCELLED:
        return setze_status(job_id, STATUS_CANCELLED, verzeichnis)
    freigeben(job_id, GUELTIG, verzeichnis)
    if ziel == STATUS_QUEUED:
        return lies_job(job_id, verzeichnis)
    setze_status(job_id, STATUS_RUNNING, verzeichnis)
    if ziel == STATUS_RUNNING:
        return lies_job(job_id, verzeichnis)
    if ziel in (STATUS_DONE, STATUS_ERROR):
        return setze_status(job_id, ziel, verzeichnis)
    raise AssertionError(f"kein Weg nach {ziel!r} vorgesehen")


# --------------------------------------------------------------------------------------
# 1 · Das Gate: der Status folgt allein dem Token
# --------------------------------------------------------------------------------------

def test_ohne_token_wartet_der_auftrag_auf_freigabe():
    """Der Normalfall aus dem Cockpit: einstellen ja, GPU nein."""
    satz = baue_job(job_id="vis-20260818120000-abc123", art="depth", params=PARAMS)

    assert satz["status"] == STATUS_AWAITING
    assert satz["freigegeben"] is False
    assert satz["freigegeben_am"] is None


def test_gueltiges_token_ergibt_sofort_queued():
    """Liegt die Freigabe schon vor, entfällt der Umweg über ``freigeben``."""
    satz = baue_job(job_id="vis-20260818120000-abc123", art="depth", params=PARAMS,
                    approval_token=GUELTIG)

    assert satz["status"] == STATUS_QUEUED
    assert satz["freigegeben"] is True
    assert satz["freigegeben_am"] == satz["erstellt"]


#: Die Beinahe-Token. Jedes einzelne ist ein realistischer Fehlgriff: die leere Variable,
#: das fehlende Argument, das abgeschnittene Log, das falsch abgetippte Präfix, die
#: Kleinschreibung aus einer normalisierenden Zwischenschicht.
UNGUELTIG = [
    ("leer", ""),
    ("None", None),
    ("nur das Präfix", TOKEN_PRAEFIX),
    ("Präfix mit Leerzeichen-Rest", TOKEN_PRAEFIX + "   "),
    ("fremdes Wort", "FOO"),
    ("kleingeschrieben", "confirmed_render_ja"),
    ("gemischt", "Confirmed_Render_ja"),
    ("Präfix nicht am Anfang", "bitte " + TOKEN_PRAEFIX + "ja"),
    ("kein str", 1),
    ("bool", True),
]


@pytest.mark.parametrize("name, token", UNGUELTIG, ids=[n for n, _ in UNGUELTIG])
def test_ungueltige_token_gelten_nicht(name, token):
    """``ist_gueltiges_token`` ist ohne Toleranz — anders als ``normalize_up_axis``.

    Dort war Nachsicht richtig, weil zwei Erzeuger dasselbe meinten. Hier wäre sie eine
    Aufweichung des einzigen Gates, das die Hardware schützt.
    """
    assert ist_gueltiges_token(token) is False


@pytest.mark.parametrize("name, token", UNGUELTIG, ids=[n for n, _ in UNGUELTIG])
def test_ungueltige_token_fuehren_nie_zu_queued(name, token):
    """Fail-closed: kein Fehler, aber auch keine Freigabe."""
    satz = baue_job(job_id="vis-20260818120000-abc123", art="depth", params=PARAMS,
                    approval_token=token)

    assert satz["status"] == STATUS_AWAITING
    assert satz["freigegeben"] is False


def test_gueltiges_token_braucht_nur_ein_zeichen_rest():
    """Die Grenze liegt genau zwischen ``PRÄFIX`` und ``PRÄFIX + 1 Zeichen``."""
    assert ist_gueltiges_token(TOKEN_PRAEFIX) is False
    assert ist_gueltiges_token(TOKEN_PRAEFIX + "x") is True


def test_setze_status_kann_queued_nicht_setzen(tmp_path):
    """Die zweite Hälfte des Gates.

    Ohne diese Sperre wäre ``freigeben`` reine Zierde: Wer ``setze_status`` erreicht,
    erreicht auch ``setze_status(…, "queued")`` — und hätte sich die Freigabe selbst
    erteilt.
    """
    _job(tmp_path)

    with pytest.raises(UebergangError, match="freigeben"):
        setze_status("vis-20260818120000-abc123", STATUS_QUEUED, tmp_path)

    assert lies_job("vis-20260818120000-abc123", tmp_path)["status"] == STATUS_AWAITING


def test_freigeben_hebt_den_auftrag_nach_queued(tmp_path):
    """Der einzige erlaubte Weg dorthin — und er wird auf der Platte sichtbar."""
    _job(tmp_path)

    satz = freigeben("vis-20260818120000-abc123", GUELTIG, tmp_path)

    assert satz["status"] == STATUS_QUEUED
    assert satz["freigegeben"] is True
    assert lies_job("vis-20260818120000-abc123", tmp_path)["status"] == STATUS_QUEUED


@pytest.mark.parametrize("name, token", UNGUELTIG, ids=[n for n, _ in UNGUELTIG])
def test_freigeben_mit_ungueltigem_token_laesst_die_platte_unberuehrt(tmp_path, name, token):
    """Nicht nur der Rückgabewert zählt — die Datei darf sich kein Byte bewegen.

    Ein ``freigeben``, das wirft *und* nebenbei schreibt, wäre schlimmer als eines, das
    still gelingt: Der Aufrufer sähe den Fehler und hielte den Auftrag für unverändert.
    """
    _job(tmp_path)
    datei = tmp_path / "vis-20260818120000-abc123.json"
    vorher = datei.read_bytes()

    with pytest.raises(JobError):
        freigeben("vis-20260818120000-abc123", token, tmp_path)

    assert datei.read_bytes() == vorher
    assert lies_job("vis-20260818120000-abc123", tmp_path)["status"] == STATUS_AWAITING


def test_freigeben_ist_nicht_wiederholbar(tmp_path):
    """Eine zweite Freigabe auf einem freigegebenen Auftrag ist ein Befund, kein No-op.

    Sie hiesse, dass zwei Stellen dasselbe Gate bedienen — das gehört gemeldet, nicht
    weggelächelt.
    """
    _bringe_auf(tmp_path, STATUS_QUEUED)

    with pytest.raises(UebergangError):
        freigeben("vis-20260818120000-abc123", GUELTIG, tmp_path)


def test_freigeben_eines_abgebrochenen_auftrags_scheitert(tmp_path):
    """Ein abgebrochener Auftrag ist Endzustand — auch ein gültiges Token holt ihn nicht zurück."""
    _bringe_auf(tmp_path, STATUS_CANCELLED)

    with pytest.raises(UebergangError):
        freigeben("vis-20260818120000-abc123", GUELTIG, tmp_path)


# --------------------------------------------------------------------------------------
# 2 · Der Statusgraph
# --------------------------------------------------------------------------------------

def test_alle_status_sind_vollstaendig_und_im_graph():
    """Selbstprobe: Der Graph deckt genau die bekannten Status ab — kein toter Zustand."""
    assert set(jobs.UEBERGAENGE) == set(ALLE_STATUS)
    for ziele in jobs.UEBERGAENGE.values():
        assert ziele <= ALLE_STATUS


@pytest.mark.parametrize("von, nach", [
    (STATUS_AWAITING, STATUS_CANCELLED),
    (STATUS_QUEUED, STATUS_RUNNING),
    (STATUS_QUEUED, STATUS_CANCELLED),
    (STATUS_RUNNING, STATUS_DONE),
    (STATUS_RUNNING, STATUS_ERROR),
    (STATUS_RUNNING, STATUS_CANCELLED),
])
def test_erlaubter_uebergang(tmp_path, von, nach):
    """Jeder erlaubte Übergang ausser ``awaiting → queued`` (der hat einen eigenen Test)."""
    _bringe_auf(tmp_path, von)

    satz = setze_status("vis-20260818120000-abc123", nach, tmp_path)

    assert satz["status"] == nach
    assert lies_job("vis-20260818120000-abc123", tmp_path)["status"] == nach


@pytest.mark.parametrize("von, nach", [
    (STATUS_AWAITING, STATUS_RUNNING),      # das Gate überspringen
    (STATUS_AWAITING, STATUS_DONE),         # fertig, ohne je gelaufen zu sein
    (STATUS_QUEUED, STATUS_DONE),           # dito, eine Stufe später
    (STATUS_DONE, STATUS_RUNNING),          # ein zweiter Lauf auf alter Freigabe
    (STATUS_DONE, STATUS_CANCELLED),        # Endzustand ist Endzustand
    (STATUS_ERROR, STATUS_RUNNING),         # Wiederholung heisst neu einstellen
    (STATUS_CANCELLED, STATUS_RUNNING),
    (STATUS_RUNNING, STATUS_AWAITING),      # rückwärts gibt es nicht
])
def test_verbotener_uebergang(tmp_path, von, nach):
    """Alles ausserhalb des Graphen ist ``UebergangError`` — und ändert nichts."""
    _bringe_auf(tmp_path, von)

    with pytest.raises(UebergangError):
        setze_status("vis-20260818120000-abc123", nach, tmp_path)

    assert lies_job("vis-20260818120000-abc123", tmp_path)["status"] == von


def test_unbekannter_status_wird_abgewiesen(tmp_path):
    """Ein Tippfehler im Status ergäbe einen Auftrag, den kein Scheduler je wieder anfasst."""
    _job(tmp_path)

    with pytest.raises(JobError, match="unbekannter Status"):
        setze_status("vis-20260818120000-abc123", "fertig", tmp_path)


def test_ergebnis_und_fehler_werden_mitgeschrieben(tmp_path):
    """Was der Lauf hinterlässt, gehört in denselben Satz — sonst sucht man es woanders."""
    _bringe_auf(tmp_path, STATUS_RUNNING)

    satz = setze_status("vis-20260818120000-abc123", STATUS_DONE, tmp_path,
                        ergebnis={"depth_png": "/synthetisch/out/depth.png"})

    assert satz["ergebnis"] == {"depth_png": "/synthetisch/out/depth.png"}
    assert lies_job("vis-20260818120000-abc123", tmp_path)["ergebnis"]["depth_png"].endswith(".png")


def test_fehlertext_ueberlebt_den_wechsel_nach_error(tmp_path):
    _bringe_auf(tmp_path, STATUS_RUNNING)

    satz = setze_status("vis-20260818120000-abc123", STATUS_ERROR, tmp_path,
                        fehler="Blender endete mit Code 1")

    assert "Code 1" in lies_job("vis-20260818120000-abc123", tmp_path)["fehler"]
    assert satz["status"] == STATUS_ERROR


def test_verlauf_haelt_fest_wann_was_geschah(tmp_path):
    """``geaendert`` allein überschriebe die Vorgeschichte.

    Die Frage, die man später wirklich stellt, ist: wie lange lag der Auftrag, und wie
    lange lief er. Ohne Verlauf ist sie unbeantwortbar.
    """
    _bringe_auf(tmp_path, STATUS_DONE)

    satz = lies_job("vis-20260818120000-abc123", tmp_path)
    stationen = [eintrag["status"] for eintrag in satz["verlauf"]]

    assert stationen == [STATUS_AWAITING, STATUS_QUEUED, STATUS_RUNNING, STATUS_DONE]
    assert all(eintrag["zeit"] for eintrag in satz["verlauf"])
    assert satz["geaendert"] >= satz["erstellt"]


# --------------------------------------------------------------------------------------
# 3 · Ablage: Rundlauf, Liste, Kennungen
# --------------------------------------------------------------------------------------

def test_rundlauf_schreiben_lesen(tmp_path):
    """Was hineingeht, kommt heraus — über eine Datei, nicht über ein Objekt im Speicher."""
    satz = baue_job(job_id="vis-20260818120000-abc123", art="depth", params=PARAMS)
    pfad = schreibe_job(satz, tmp_path)

    assert pfad == tmp_path / "vis-20260818120000-abc123.json"
    assert lies_job("vis-20260818120000-abc123", tmp_path) == satz


def test_schreiben_legt_das_verzeichnis_an(tmp_path):
    """Vor dem ersten Auftrag gibt es die Ablage nicht — das ist kein Fehlerfall."""
    ziel = tmp_path / "neu" / "tiefer"

    schreibe_job(baue_job(job_id="a1", art="depth", params={}), ziel)

    assert (ziel / "a1.json").exists()


def test_params_werden_kopiert(tmp_path):
    """Der Aufrufer darf seinen Dict weiterverwenden, ohne den Auftrag nachträglich zu ändern."""
    veraenderlich = {"aufloesung": 512}
    satz = baue_job(job_id="a1", art="depth", params=veraenderlich)
    veraenderlich["aufloesung"] = 4096

    assert satz["params"]["aufloesung"] == 512


def test_lies_job_meldet_fehlenden_auftrag(tmp_path):
    with pytest.raises(JobError, match="nicht gefunden"):
        lies_job("vis-20260818120000-abc123", tmp_path)


def test_lies_job_meldet_kaputte_datei(tmp_path):
    """Ein unlesbarer Auftrag wird gemeldet, nicht als leerer Satz durchgereicht."""
    (tmp_path / "a1.json").write_text("{kein json", encoding="utf-8")

    with pytest.raises(JobError, match="kein lesbares JSON"):
        lies_job("a1", tmp_path)


def test_liste_jobs_ohne_und_mit_filter(tmp_path):
    """Der ``query``-Teil der Dreiteilung: lesen, filtern, nichts anfassen."""
    _job(tmp_path, "vis-20260818120000-aaaaaa")
    _job(tmp_path, "vis-20260818120001-bbbbbb")
    _job(tmp_path, "vis-20260818120002-cccccc")
    freigeben("vis-20260818120001-bbbbbb", GUELTIG, tmp_path)
    setze_status("vis-20260818120002-cccccc", STATUS_CANCELLED, tmp_path)

    alle = liste_jobs(tmp_path)
    wartend = liste_jobs(tmp_path, status=STATUS_AWAITING)
    bereit = liste_jobs(tmp_path, status=STATUS_QUEUED)

    assert len(alle) == 3
    assert [s["job_id"] for s in wartend] == ["vis-20260818120000-aaaaaa"]
    assert [s["job_id"] for s in bereit] == ["vis-20260818120001-bbbbbb"]
    assert liste_jobs(tmp_path, status=STATUS_RUNNING) == []


def test_liste_jobs_ist_nach_erstellzeit_sortiert(tmp_path):
    """Die Reihenfolge, in der ein Scheduler abarbeiten will — und sie muss stabil sein."""
    for kennung in ("vis-20260818120002-cccccc", "vis-20260818120000-aaaaaa"):
        _job(tmp_path, kennung)

    kennungen = [s["job_id"] for s in liste_jobs(tmp_path)]

    assert kennungen == sorted(kennungen)


def test_liste_jobs_auf_leerem_verzeichnis(tmp_path):
    """Ein Scheduler, der im Leerlauf nachschaut, soll nicht abstürzen."""
    assert liste_jobs(tmp_path) == []
    assert liste_jobs(tmp_path / "gibtsnicht") == []


def test_liste_jobs_weist_unbekannten_filter_ab(tmp_path):
    """Ein Tippfehler im Filter gäbe sonst still eine leere Liste — die sieht aus wie „nichts zu tun"."""
    with pytest.raises(JobError, match="unbekannter Status"):
        liste_jobs(tmp_path, status="wartend")


def test_neue_job_id_erfuellt_das_muster():
    kennung = neue_job_id()

    assert JOB_ID_MUSTER.fullmatch(kennung), kennung
    assert kennung.startswith("vis-")


def test_neue_job_id_ist_mit_injizierten_werten_reproduzierbar():
    """Ohne Injektion wäre nur das Muster prüfbar — also die Hälfte."""
    assert neue_job_id("20260818120000", "abc123") == "vis-20260818120000-abc123"
    assert neue_job_id(zeitstempel="20260818120000", zufall="000000") == "vis-20260818120000-000000"


def test_neue_job_id_ist_ohne_injektion_verschieden():
    """Zwei Aufträge in derselben Sekunde sind der Normalfall, nicht die Ausnahme."""
    assert len({neue_job_id("20260818120000") for _ in range(50)}) > 1


@pytest.mark.parametrize("zeitstempel, zufall", [
    ("2026-08-18", "abc123"),      # mit Trennern statt 14 Ziffern
    ("2026081812000", "abc123"),   # eine Ziffer zu wenig
    ("20260818120000", "ABC123"),  # Hex gross geschrieben
    ("20260818120000", "xyz123"),  # gar kein Hex
    ("20260818120000", "abc12"),   # zu kurz
])
def test_neue_job_id_weist_falsche_teile_ab(zeitstempel, zufall):
    """Lieber hier auffallen als in einer Kennung, die kein Scheduler wiedererkennt."""
    with pytest.raises(JobError):
        neue_job_id(zeitstempel, zufall)


# --------------------------------------------------------------------------------------
# 4 · Pfad-Trickserei
# --------------------------------------------------------------------------------------

#: Kennungen, die aus dem Auftragsverzeichnis hinauszeigen. Sie sind kein Hirngespinst:
#: Die ``job_id`` kommt im Betrieb über MCP herein, also aus einem Sprachmodell.
BOESE_KENNUNGEN = [
    "../boese",
    "a/b",
    "../../etc/passwd",
    "/absolut",
    "..",
    ".",
    ".versteckt",
    "a\\b",
    "",
]


@pytest.mark.parametrize("kennung", BOESE_KENNUNGEN, ids=repr)
def test_boese_kennung_kann_nicht_gebaut_werden(kennung):
    with pytest.raises(JobError):
        baue_job(job_id=kennung, art="depth", params=PARAMS)


@pytest.mark.parametrize("kennung", BOESE_KENNUNGEN, ids=repr)
def test_boese_kennung_kann_nicht_gelesen_werden(tmp_path, kennung):
    with pytest.raises(JobError):
        lies_job(kennung, tmp_path)


@pytest.mark.parametrize("kennung", BOESE_KENNUNGEN, ids=repr)
def test_boese_kennung_kann_nicht_geschrieben_werden(tmp_path, kennung):
    """Auch am Konstruktor vorbei: ``schreibe_job`` prüft selbst, statt zu vertrauen.

    Ein von Hand gebauter Satz ist der realistische Weg — genau so würde ein Aufrufer
    einen Auftrag „reparieren", der über MCP hereinkam.
    """
    satz = {"job_id": kennung, "art": "depth", "params": {}, "status": STATUS_AWAITING}

    with pytest.raises(JobError):
        schreibe_job(satz, tmp_path)


def test_kein_schreibzugriff_ausserhalb_des_verzeichnisses(tmp_path):
    """Der Beweis am Dateisystem: nach dem abgewiesenen Versuch liegt draussen nichts."""
    ablage = tmp_path / "jobs"
    ablage.mkdir()
    daneben = tmp_path / "daneben.json"

    with pytest.raises(JobError):
        schreibe_job({"job_id": "../daneben", "art": "depth", "params": {},
                      "status": STATUS_AWAITING}, ablage)

    assert not daneben.exists()
    assert list(ablage.iterdir()) == []


def test_boese_kennung_taucht_in_der_liste_nicht_auf(tmp_path):
    """Eine von Hand danebengelegte Datei ist kein Auftrag dieses Verzeichnisses."""
    (tmp_path / "unterordner").mkdir()
    (tmp_path / "unterordner" / "a1.json").write_text("{}", encoding="utf-8")

    assert liste_jobs(tmp_path) == []


# --------------------------------------------------------------------------------------
# 5 · Atomizität
# --------------------------------------------------------------------------------------

def test_gescheitertes_schreiben_hinterlaesst_keine_datei(tmp_path):
    """Ein nicht serialisierbarer Wert bricht mitten im Schreiben ab — und zwar echt.

    ``json.dump`` schreibt fortlaufend: Bis zum ``object()`` in ``params`` steht bereits
    ein guter Teil des Satzes in der temporären Datei. Genau dieser Rest darf nicht
    liegen bleiben — weder als ``.json`` noch als temporäre Datei, denn ein Scheduler,
    der aufräumt statt zu prüfen, hielte ihn für einen Auftrag.
    """
    satz = baue_job(job_id="a1", art="depth", params={"objekt": object()})

    with pytest.raises(JobError, match="nicht als JSON darstellbar"):
        schreibe_job(satz, tmp_path)

    assert list(tmp_path.iterdir()) == [], "Rest im Verzeichnis — auch temporäre Reste zählen"


def test_gescheitertes_ersetzen_hinterlaesst_keine_datei(tmp_path, monkeypatch):
    """Zweite Bruchstelle: Der Inhalt steht, aber das Umhängen des Namens scheitert."""
    def kaputt(_alt, _neu):
        raise OSError("Platte voll")

    monkeypatch.setattr(jobs.os, "replace", kaputt)

    with pytest.raises(OSError, match="Platte voll"):
        schreibe_job(baue_job(job_id="a1", art="depth", params=PARAMS), tmp_path)

    assert list(tmp_path.iterdir()) == []


def test_gescheiterte_aktualisierung_laesst_den_alten_auftrag_stehen(tmp_path):
    """Der eigentliche Zweck von ``os.replace``: nie ein halber Auftrag, immer einer.

    Scheitert das Neuschreiben, liest ein gleichzeitig laufender Scheduler weiterhin den
    **alten, vollständigen** Satz — nicht eine geleerte Datei.
    """
    _job(tmp_path)
    vorher = (tmp_path / "vis-20260818120000-abc123.json").read_bytes()

    satz = lies_job("vis-20260818120000-abc123", tmp_path)
    satz["params"]["objekt"] = object()
    with pytest.raises(JobError):
        schreibe_job(satz, tmp_path)

    assert (tmp_path / "vis-20260818120000-abc123.json").read_bytes() == vorher
    assert list(tmp_path.iterdir()) == [tmp_path / "vis-20260818120000-abc123.json"]


def test_abgelegter_auftrag_ist_vollstaendiges_json(tmp_path):
    """Die Datei muss für fremde Prozesse lesbar sein — der Scheduler ist nicht dieses Python."""
    _job(tmp_path)

    roh = (tmp_path / "vis-20260818120000-abc123.json").read_text(encoding="utf-8")
    satz = json.loads(roh)

    assert satz["schema"] == jobs.JOB_SCHEMA_ID
    assert satz["status"] in ALLE_STATUS
    assert roh.endswith("\n")


# --------------------------------------------------------------------------------------
# 6 · Nebenabreden
# --------------------------------------------------------------------------------------

def test_idle_window_only_wird_nur_mitgefuehrt(tmp_path):
    """Das Feld wird geschrieben, aber nicht ausgewertet — der Scheduler kommt später.

    Es darf insbesondere nichts am Status ändern: Wer ``idle_window_only=False`` setzt,
    umgeht damit keine Freigabe.
    """
    ohne = _job(tmp_path, "a1", idle_window_only=False)
    mit = _job(tmp_path, "a2")

    assert ohne["idle_window_only"] is False
    assert mit["idle_window_only"] is True
    assert ohne["status"] == mit["status"] == STATUS_AWAITING
    assert lies_job("a1", tmp_path)["idle_window_only"] is False


def test_das_token_landet_nie_auf_der_platte(tmp_path):
    """Ein Token ist eine Befugnis, kein Protokolleintrag.

    Die Auftragsdatei ist für jeden lesbar, der das Verzeichnis sieht. Läge das Token
    darin, wäre die Freigabe mit ihr weitergereicht — abgelegt wird darum nur die
    *Tatsache* der Freigabe.
    """
    _job(tmp_path, token=GUELTIG)
    freigegeben = _job(tmp_path, "a2")
    freigeben("a2", GUELTIG, tmp_path)

    for datei in tmp_path.glob("*.json"):
        roh = datei.read_text(encoding="utf-8")
        assert TOKEN_PRAEFIX not in roh, f"{datei.name} trägt das Freigabe-Token"
    assert lies_job("a2", tmp_path)["freigegeben"] is True
    assert freigegeben["job_id"] == "a2"


def test_baue_job_weist_unbrauchbare_eingaben_ab():
    with pytest.raises(JobError, match="art"):
        baue_job(job_id="a1", art="", params=PARAMS)
    with pytest.raises(JobError, match="params"):
        baue_job(job_id="a1", art="depth", params=["keine", "dict"])


def test_jobs_bleibt_reine_stdlib():
    """Regel 1, 2 und 4: keine Laufzeitabhängigkeit, kein ``bpy``, kein ``ifcopenshell``.

    ``test_prozessgrenze.py`` bewacht das für den ganzen Kern; hier steht es noch einmal
    für dieses Modul, weil die Auftragsablage die Stelle ist, an der später die
    Versuchung am grössten ist, eine Datenbank oder eine Warteschlange hereinzuholen.
    """
    quelle = Path(jobs.__file__).read_text(encoding="utf-8")
    baum = re.findall(r"^\s*(?:import|from)\s+([\w.]+)", quelle, flags=re.MULTILINE)
    fremd = {name.split(".")[0] for name in baum} - {
        "__future__", "copy", "json", "os", "re", "secrets", "tempfile", "datetime", "pathlib",
    }

    assert not fremd, f"jobs.py zieht {sorted(fremd)} herein"
