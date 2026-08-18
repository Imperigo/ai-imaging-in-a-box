"""LoRA-Stiltraining ohne GPU, ohne Trainer, ohne ein einziges Gewicht.

`lora.py` ist nach seinem eigenen Modulkopf die **einzige Stelle im Projekt, an der
Regel 1 und Regel 3 gleichzeitig greifen** — und beide sollen dort *ausführbar* sein,
nicht bloss aufgeschrieben. Genau das ist der Gegenstand dieser Datei. Sie prüft zwei
Behauptungen, alles andere ist Beiwerk:

**A · Ein LoRA erbt die Lizenz seiner Grundlage.** Ein Auftrag auf FLUX-dev wird
abgelehnt, *bevor* gerechnet wird. Die Probe darauf ist nicht die Zeichenkette
``"abgelehnt"``, sondern die Attrappe, die **nie gerufen** wurde: Ein Vertrag, der erst
nach den GPU-Stunden greift, ist keiner. Parametrisiert wird über die echte Registry und
nicht über eine Namensliste — kommt ein Non-Commercial-Modell dazu, greift der Test von
selbst.

**B · Trainingsdaten und Ergebnis gehören nicht ins Repo.** Geprüft wird nicht nur der
gerade Weg, sondern die Umwege: relativer Pfad, ``..``, symbolische Verknüpfung. Jede
Ablehnungsprobe hat eine Gegenprobe mit einem Pfad **ausserhalb** — ohne sie wäre der
Test auch grün, wenn ``liegt_im_repo`` immer ``True`` gäbe.

Dazu kommen die Prozessgrenze (``finde_trainer_python`` fällt nie auf ``sys.executable``
zurück), die Trainer-Registry und die Parameterprüfung.

Es läuft **kein** Trainer: kein ``torch``, keine GPU, kein Netz. Alles geht über die
``_starte``-Naht und ``monkeypatch``. Alle Pfade sind erfunden und synthetisch (Regel 3);
kein Bild, kein Büro-, Kunden- oder Projektname taucht hier auf.

Vier Befunde stehen weiter unten unter „BEFUNDE" — Stellen, an denen das Modul weniger
zusichert, als man ihm beim Lesen zutraut. Sie sind hier als *beobachtetes* Verhalten
festgehalten, nicht als gewünschtes, und im Schlussbericht der Sitzung genannt.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from conftest import REPO

from aiimaging import backbone, lizenzquelle, lora, render
from aiimaging.lora import (
    TRAINER,
    VORGABE_TRAINER,
    LoraAuftrag,
    LoraError,
    baue_kommando,
    finde_trainer_python,
    finde_trainer_wurzel,
    hole_trainer,
    liegt_im_repo,
    lizenz_des_ergebnisses,
    pruefe_auftrag,
    pruefe_modell_wurzel,
    trainiere,
)

#: Zwei Pfade weit ausserhalb des Repos. Sie müssen nicht existieren — ``pruefe_auftrag``
#: fragt nach der *Lage*, nicht nach dem Inhalt. Das ist Absicht: Der Rechner, der prüft,
#: ist nicht der Rechner, der trainiert.
DATENSATZ_AUSSERHALB = "/data/stilbilder"
AUSGABE_AUSSERHALB = "/data/loras"

#: Attrappen für die beiden Umgebungsvariablen. Gestartet wird davon nie etwas.
TRAINER_PYTHON = "/attrappe/venv-lora/bin/python"
TRAINER_WURZEL = "/attrappe/kohya"


# --------------------------------------------------------------------------------------
# Die Registry als Testquelle — nicht als abgeschriebene Namensliste
# --------------------------------------------------------------------------------------

def _nach_lizenzlage() -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """(nicht zulässig, zulässig, mit Regel-1-Spannung) — direkt aus ``backbone``.

    Über die Registry statt über eine Namensliste: Eine Liste im Test veraltet still,
    sobald ein Modell dazukommt. Die Registry tut das nicht.
    """
    nein, ja, spannung = [], [], []
    for name in sorted(backbone.BACKBONES):
        lage = backbone.pruefe_lizenz(name)
        (ja if lage["zulaessig"] else nein).append(name)
        if lage.get("regel_1_spannung"):
            spannung.append(name)
    return tuple(nein), tuple(ja), tuple(spannung)


NICHT_ZULAESSIG, ZULAESSIG, MIT_SPANNUNG = _nach_lizenzlage()


# --------------------------------------------------------------------------------------
# Doppelgänger und Werkzeug
# --------------------------------------------------------------------------------------

class Ergebnis:
    """Doppelgänger eines ``subprocess.CompletedProcess`` — nur, was die Naht ausliest."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


class Attrappe:
    """Ersatz für ``_starte``: merkt sich die Kommandos, statt einen Trainer zu starten.

    ``kommandos`` ist das eigentliche Beweisstück dieser Datei. Bleibt die Liste bei
    einer Ablehnung leer, dann ist Regel 1 wirklich *vor* der ersten GPU-Sekunde
    wirksam geworden — und nicht erst in der Formulierung des Ergebnisses.
    """

    def __init__(self, ergebnis=None, *, nebenwirkung=None):
        self.ergebnis = ergebnis or Ergebnis()
        self.nebenwirkung = nebenwirkung
        self.kommandos: list[list[str]] = []
        self.timeouts: list[int] = []

    def __call__(self, cmd, timeout):
        self.kommandos.append(list(cmd))
        self.timeouts.append(timeout)
        if self.nebenwirkung is not None:
            self.nebenwirkung(list(cmd))
        return self.ergebnis

    @property
    def kommando(self) -> list[str]:
        assert len(self.kommandos) == 1, \
            f"erwartet: genau ein Aufruf, war {len(self.kommandos)}"
        return self.kommandos[0]

    @property
    def wurde_gerufen(self) -> bool:
        return bool(self.kommandos)


def verweigerer(cmd, timeout):
    """``_starte``, das nie gerufen werden darf — belegt einen Abbruch **davor**."""
    raise AssertionError(f"Es wurde gerechnet, obwohl der Vertrag brach: {cmd}")


def legt_lora_ab(name: str = "haus-stil.safetensors"):
    """Nebenwirkung: schreibt eine Platzhalterdatei dorthin, wo der LoRA erwartet wird.

    Der Inhalt ist bedeutungslos — ``trainiere`` prüft Existenz, nicht Gewichte. Genau
    das ist der Punkt: Ein Trainer, der 0 meldet und nichts schreibt, ist gescheitert.
    """
    def nebenwirkung(cmd: list[str]) -> None:
        ziel = Path(cmd[cmd.index("--output_dir") + 1])
        ziel.mkdir(parents=True, exist_ok=True)
        (ziel / name).write_bytes(b"kein echtes Gewicht")
    return nebenwirkung


def auftrag(**kw) -> LoraAuftrag:
    """Ein in jeder Hinsicht gültiger Auftrag; ``kw`` überschreibt einzelne Felder."""
    felder = {
        "basis": backbone.VORGABE_BACKBONE,
        "datensatz": DATENSATZ_AUSSERHALB,
        "ausgabe": AUSGABE_AUSSERHALB,
    }
    felder.update(kw)
    return LoraAuftrag(**felder)


@pytest.fixture(autouse=True)
def ohne_geerbte_umgebung(monkeypatch):
    """Kein Test erbt eine gesetzte Variable aus der Umgebung des Aufrufers.

    Ohne das wäre diese Datei auf einem Rechner mit eingerichtetem Trainer-venv grün
    und hier rot — oder umgekehrt. Ein Test, dessen Ergebnis vom Rechner abhängt,
    belegt nichts.
    """
    for name in (lora.UMGEBUNG_TRAINER_PYTHON, lora.UMGEBUNG_TRAINER_WURZEL,
                 render.UMGEBUNG_MODELLE):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def trainer_umgebung(monkeypatch):
    """Zwei Pfade, die so tun, als läge ein Trainer-venv bereit — ausgeführt wird nie."""
    monkeypatch.setenv(lora.UMGEBUNG_TRAINER_PYTHON, TRAINER_PYTHON)
    monkeypatch.setenv(lora.UMGEBUNG_TRAINER_WURZEL, TRAINER_WURZEL)


# ======================================================================================
# A · REGEL 1 IST AUSFÜHRBAR — ein LoRA erbt die Lizenz seiner Grundlage
# ======================================================================================

def test_gegenprobe_die_registry_fuehrt_ueberhaupt_ausgeschlossene_modelle():
    """Ohne diese Probe prüften alle Ablehnungstests nur, dass ein Tippfehler auffällt.

    Die Registry führt die beiden FLUX-dev-Einträge bewusst mit, damit die Ablehnung an
    der **Lizenz** hängt und nicht an einem unbekannten Namen (siehe ``backbone.py``).
    """
    assert NICHT_ZULAESSIG, "Vorbedingung: die Registry kennt nicht zulässige Modelle"
    assert {"flux1-dev", "flux2-dev"} <= set(NICHT_ZULAESSIG)
    assert ZULAESSIG, "Vorbedingung: die Registry kennt auch zulässige Modelle"


@pytest.mark.parametrize("basis", ["flux1-dev", "flux2-dev"])
def test_lora_auf_non_commercial_ist_nicht_verkaufbar(basis):
    """`CLAUDE.md` wörtlich: der Ausschluss gilt „auch für daraus abgeleitete LoRAs"."""
    erbe = lizenz_des_ergebnisses(basis)

    assert erbe["verkaufbar"] is False
    assert erbe["basis"] == basis
    assert "Non-Commercial" in erbe["lora_lizenz"]


@pytest.mark.parametrize("basis", ["flux1-dev", "flux2-dev"])
def test_begruendung_nimmt_die_beiden_ueblichen_einwaende_vorweg(basis):
    """„Aber es sind unsere Bilder" und „aber wir haben dafür bezahlt" — beides zählt nicht.

    Genau diese zwei Sätze fallen, wenn eine Ablehnung teuer wird. Sie stehen darum in
    der Begründung, nicht nur im Modulkopf.
    """
    begruendung = lizenz_des_ergebnisses(basis)["begruendung"]

    assert "Trainingsbilder" in begruendung
    assert "Rechenzeit" in begruendung
    assert "NICHT verwertbar" in begruendung


def test_lora_auf_apache_grundlage_ist_verkaufbar():
    """Die Gegenprobe: Ohne sie wäre die Prüfung auch grün, wenn sie alles ablehnte."""
    erbe = lizenz_des_ergebnisses("qwen-image-edit-2511")

    assert erbe["verkaufbar"] is True
    assert erbe["lora_lizenz"] == "Apache-2.0"
    assert erbe["regel_1_spannung"] is None


@pytest.mark.parametrize("basis", NICHT_ZULAESSIG)
def test_jedes_nicht_zulaessige_modell_ergibt_einen_unverkaeuflichen_lora(basis):
    """Über die Registry parametrisiert: Kommt ein Modell dazu, greift der Test von selbst.

    Das ist der Unterschied zwischen einer ausführbaren Regel und einer abgeschriebenen
    Liste — die Liste veraltet still, die Registry nicht.
    """
    assert backbone.pruefe_lizenz(basis)["zulaessig"] is False
    assert lizenz_des_ergebnisses(basis)["verkaufbar"] is False


@pytest.mark.parametrize("basis", ZULAESSIG)
def test_jedes_zulaessige_modell_ergibt_einen_verkaeuflichen_lora(basis):
    """Die Kehrseite: Was die Registry zulässt, darf hier nicht zusätzlich scheitern."""
    assert lizenz_des_ergebnisses(basis)["verkaufbar"] is True


@pytest.mark.parametrize("basis", sorted(backbone.BACKBONES))
def test_der_lora_traegt_genau_die_lizenz_seiner_grundlage(basis):
    """Ein LoRA ist eine Differenz zu fremden Gewichten — er erfindet keine eigene Lizenz."""
    erbe = lizenz_des_ergebnisses(basis)
    assert erbe["lora_lizenz"] == erbe["basis_lizenz"] == backbone.hole(basis).lizenz


def test_unbekanntes_grundmodell_ist_ein_fehler_kein_stilles_ja():
    with pytest.raises(backbone.BackboneError):
        lizenz_des_ergebnisses("qwen-image-edit-2512")


# --------------------------------------------------------------------------------------
# A2 · Die Ablehnung greift VOR der ersten GPU-Sekunde — der eigentliche Test
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("basis", NICHT_ZULAESSIG)
def test_training_auf_non_commercial_rechnet_nicht_einmal_an(basis, trainer_umgebung):
    """Der Kern der Sache: ``status`` stimmt **und** die Attrappe wurde nie gerufen.

    Ohne den zweiten Teil prüfte dieser Test nur, dass eine Zeichenkette stimmt. Eine
    Lizenzprüfung, die erst nach dem Lauf greift, kostet die GPU-Stunden trotzdem —
    und genau das beschreibt der Modulkopf als den teuren Normalfall.
    """
    attrappe = Attrappe()

    ergebnis = trainiere(auftrag(basis=basis), _starte=attrappe)

    assert ergebnis["status"] == "abgelehnt"
    assert attrappe.wurde_gerufen is False, "Es wurde gerechnet, obwohl Regel 1 griff"
    assert ergebnis["lora"] is None
    assert any(m.startswith("REGEL 1") for m in ergebnis["maengel"])


def test_ablehnung_auch_ohne_naht_startet_nichts(trainer_umgebung):
    """Zweite Fassung derselben Frage, mit einem ``_starte``, das laut wird statt zu zählen."""
    ergebnis = trainiere(auftrag(basis="flux1-dev"), _starte=verweigerer)
    assert ergebnis["status"] == "abgelehnt"


def test_baue_kommando_baut_fuer_non_commercial_gar_kein_kommando(trainer_umgebung):
    """Der naheliegende Umweg an ``trainiere`` vorbei ist ebenfalls zu.

    ``baue_kommando`` ruft dieselbe Prüfung und verweigert die Kommandozeile — sonst
    liesse sich ein verbotener Lauf zusammenbauen und von Hand starten.
    """
    with pytest.raises(LoraError, match="REGEL 1"):
        baue_kommando(auftrag(basis="flux1-dev"))


def test_regel_1_steht_vor_allen_anderen_maengeln():
    """Die Reihenfolge ist bindend (Docstring): Lizenz zuerst, auch wenn sonst nichts stimmt.

    Ein Auftrag auf verbotener Grundlage soll nicht am Rang scheitern und dadurch nach
    dem Korrigieren des Rangs plötzlich „gehen"."""
    maengel = pruefe_auftrag(auftrag(basis="flux1-dev", rang=0, lernrate=7))

    assert maengel[0].startswith("REGEL 1")
    assert len(maengel) >= 3, "die übrigen Mängel sollen trotzdem alle genannt werden"


def test_ablehnung_traegt_die_parameter_ins_protokoll(trainer_umgebung):
    """Auch eine Ablehnung ist ein Vorgang — im Protokoll darf nicht bloss „nein" stehen."""
    ergebnis = trainiere(auftrag(basis="flux2-dev", rang=32, seed=4711),
                         _starte=Attrappe())

    assert ergebnis["parameter"]["basis"] == "flux2-dev"
    assert ergebnis["parameter"]["rang"] == 32
    assert ergebnis["parameter"]["seed"] == 4711


# --------------------------------------------------------------------------------------
# A3 · Regel-1-Spannung — ein HINWEIS, kein Abbruch
# --------------------------------------------------------------------------------------

def test_gegenprobe_es_gibt_ueberhaupt_eintraege_mit_regel_1_spannung():
    """Ohne diese Probe wären die beiden Tests unten leer parametrisiert und still grün."""
    assert set(MIT_SPANNUNG) == {"sdxl-juggernaut", "sd35-large"}


@pytest.mark.parametrize("basis", MIT_SPANNUNG)
def test_spannung_wird_als_hinweis_genannt_und_bricht_nicht_ab(basis):
    """Zugelassen, aber nicht permissiv: gesagt wird es, entschieden wird es nicht hier.

    ``lizenzquelle.regel_1_spannung`` begründet ausführlich, warum der Widerspruch
    zwischen ``backbone`` und ``einbetter`` ein Owner-Entscheid ist. Für dieses Modul
    heisst das: sichtbar machen, nicht abbrechen.
    """
    maengel = pruefe_auftrag(auftrag(basis=basis))

    assert len(maengel) == 1
    assert maengel[0].startswith("HINWEIS (kein Abbruch)")
    assert "REGEL-1-SPANNUNG" in maengel[0]
    assert not any(m.startswith("REGEL 1:") for m in maengel)


@pytest.mark.parametrize("basis", MIT_SPANNUNG)
def test_auftrag_mit_spannung_laeuft_und_traegt_den_hinweis_mit(basis, tmp_path,
                                                                trainer_umgebung):
    """Der Lauf findet statt — und der Hinweis reist im Ergebnis mit, statt zu verfallen."""
    attrappe = Attrappe(nebenwirkung=legt_lora_ab())

    ergebnis = trainiere(auftrag(basis=basis, ausgabe=str(tmp_path / "lora")),
                         _starte=attrappe)

    assert ergebnis["status"] == "ok"
    assert attrappe.wurde_gerufen is True
    assert any("REGEL-1-SPANNUNG" in h for h in ergebnis["hinweise"])
    assert ergebnis["maengel"] == []


def test_hinweis_verhindert_das_kommando_nicht(trainer_umgebung):
    """``baue_kommando`` filtert HINWEIS-Zeilen heraus — sonst wäre SDXL unbenutzbar."""
    cmd = baue_kommando(auftrag(basis="sdxl-juggernaut"))
    assert cmd[0] == TRAINER_PYTHON


# ======================================================================================
# B · REGEL 3 IST AUSFÜHRBAR — Trainingsdaten und Ergebnis bleiben draussen
# ======================================================================================

def test_gegenprobe_pfade_ausserhalb_werden_nicht_beanstandet(tmp_path):
    """Ohne diese Probe wäre die ganze Gruppe vakuös.

    Gäbe ``liegt_im_repo`` immer ``True``, wären alle Ablehnungstests unten trotzdem
    grün — und das Modul unbenutzbar, weil jeder Datensatz abgewiesen würde.
    """
    assert liegt_im_repo(tmp_path) is False
    assert liegt_im_repo(DATENSATZ_AUSSERHALB) is False
    assert liegt_im_repo("/data/irgendwo/tief/drin") is False
    assert pruefe_auftrag(auftrag(datensatz=str(tmp_path), ausgabe=str(tmp_path))) == []


def test_das_repo_selbst_liegt_im_repo():
    """Die Kehrseite der Gegenprobe — sonst prüfte sie nur, dass die Funktion ``False`` sagt."""
    assert liegt_im_repo(REPO) is True
    assert liegt_im_repo(REPO / "docs" / "sitzungen") is True


def test_datensatz_im_repo_ist_ein_mangel():
    """Ein Stil-LoRA wird auf echten Bildern des Büros trainiert — genau die dürfen nicht rein."""
    maengel = pruefe_auftrag(auftrag(datensatz=str(REPO / "trainingsbilder")))

    assert any(m.startswith("REGEL 3") and "Datensatzverzeichnis" in m for m in maengel)
    assert any("Git-Historie" in m for m in maengel), \
        "Die Begründung soll sagen, warum späteres Löschen nicht hilft"


def test_ausgabe_im_repo_ist_ein_mangel():
    """`CLAUDE.md` nennt Bilder und darauf trainierte Gewichte in einem Satz."""
    maengel = pruefe_auftrag(auftrag(ausgabe=str(REPO / "build" / "lora")))
    assert any(m.startswith("REGEL 3") and "Ausgabeverzeichnis" in m for m in maengel)


def test_beide_lagen_werden_getrennt_gemeldet():
    """Zwei Fehler, zwei Sätze — wer beides falsch hat, soll es in einem Durchgang sehen."""
    maengel = pruefe_auftrag(auftrag(datensatz=str(REPO / "bilder"),
                                     ausgabe=str(REPO / "loras")))
    assert len([m for m in maengel if m.startswith("REGEL 3")]) == 2


def test_training_mit_datensatz_im_repo_rechnet_nicht(trainer_umgebung):
    """Regel 3 greift wie Regel 1 vor dem ersten Rechenschritt, nicht danach."""
    attrappe = Attrappe()

    ergebnis = trainiere(auftrag(datensatz=str(REPO / "bilder")), _starte=attrappe)

    assert ergebnis["status"] == "abgelehnt"
    assert attrappe.wurde_gerufen is False


# --------------------------------------------------------------------------------------
# B2 · Die Umwege — der wichtigste Teil der Gruppe
# --------------------------------------------------------------------------------------

def test_relativer_pfad_wird_mitgeschlossen(monkeypatch):
    """``docs/bilder`` ist derselbe Ort wie der absolute Pfad — nur bequemer geschrieben.

    ``monkeypatch.chdir`` steht hier nicht aus Bequemlichkeit: ``Path.resolve`` löst
    einen relativen Pfad gegen das **Arbeitsverzeichnis** auf. Ohne festgelegtes
    Arbeitsverzeichnis prüfte dieser Test, wo pytest gestartet wurde. Siehe auch den
    Befund weiter unten.
    """
    monkeypatch.chdir(REPO)

    assert liegt_im_repo("docs/bilder") is True
    assert any(m.startswith("REGEL 3")
               for m in pruefe_auftrag(auftrag(datensatz="docs/bilder")))


def test_umweg_ueber_zwei_punkte_wird_mitgeschlossen():
    """Der bequeme Weg an der Regel vorbei: aus dem Repo heraus und wieder hinein."""
    umweg = f"/tmp/../{str(REPO).lstrip('/')}/trainingsbilder"

    assert liegt_im_repo(umweg) is True
    assert any(m.startswith("REGEL 3")
               for m in pruefe_auftrag(auftrag(datensatz=umweg)))


def test_symbolische_verknuepfung_von_aussen_ins_repo_wird_mitgeschlossen(tmp_path):
    """Der Umweg, den ``Path.resolve`` tragen muss: draussen zeigen, drinnen landen.

    Der Pfad liegt dem Namen nach ausserhalb des Repos; aufgelöst liegt er drin. Genau
    darauf beruft sich der Docstring von ``liegt_im_repo``, und genau das wird hier
    nachgesehen statt geglaubt.
    """
    verknuepfung = tmp_path / "sieht-aus-wie-draussen"
    try:
        verknuepfung.symlink_to(REPO / "docs")
    except OSError as fehler:                                   # pragma: no cover
        pytest.skip(f"Dieses System erlaubt keine symbolischen Verknüpfungen: {fehler}")

    assert liegt_im_repo(verknuepfung) is True
    assert liegt_im_repo(verknuepfung / "bilder") is True
    assert any(m.startswith("REGEL 3")
               for m in pruefe_auftrag(auftrag(datensatz=str(verknuepfung))))


def test_gegenprobe_verknuepfung_aus_dem_repo_nach_draussen_ist_in_ordnung(tmp_path,
                                                                           monkeypatch):
    """Die andere Richtung ist erlaubt — der Inhalt landet ja ausserhalb.

    Ohne diese Gegenprobe könnte ``liegt_im_repo`` schlicht jede Verknüpfung ablehnen
    und der Test darüber wäre trotzdem grün.
    """
    monkeypatch.chdir(tmp_path)
    draussen = tmp_path / "echte-bilder"
    draussen.mkdir()
    verknuepfung = tmp_path / "zeigt-nach-draussen"
    try:
        verknuepfung.symlink_to(draussen)
    except OSError as fehler:                                   # pragma: no cover
        pytest.skip(f"Dieses System erlaubt keine symbolischen Verknüpfungen: {fehler}")

    assert liegt_im_repo(verknuepfung) is False


# ======================================================================================
# C · DIE PROZESSGRENZE
# ======================================================================================

def test_ohne_umgebungsvariable_gibt_es_kein_trainer_python():
    """Kein Rückfall auf ``sys.executable`` — dieselbe Entscheidung wie in ``seams.py``."""
    with pytest.raises(LoraError) as fehler:
        finde_trainer_python()

    assert lora.UMGEBUNG_TRAINER_PYTHON in str(fehler.value)


def test_die_meldung_nennt_den_grund_und_nicht_nur_die_variable():
    """Wer die Variable setzen soll, soll auch erfahren, warum der bequeme Weg zu ist.

    Ein Trainer zieht ``torch``, ``accelerate`` und die CUDA-Laufzeit nach. Liefe er im
    Produkt-Python, wäre das Produkt-venv nicht mehr das, was ``pyproject.toml`` zusagt.
    """
    with pytest.raises(LoraError) as fehler:
        finde_trainer_python()

    meldung = str(fehler.value)
    assert "torch" in meldung
    assert "CUDA" in meldung


def test_das_produkt_python_wird_niemals_zurueckgegeben(monkeypatch):
    """Ausdrücklich: auch nicht auf Umwegen, auch nicht als bequeme Voreinstellung."""
    with pytest.raises(LoraError):
        finde_trainer_python()

    monkeypatch.setenv(lora.UMGEBUNG_TRAINER_PYTHON, TRAINER_PYTHON)
    gefunden = finde_trainer_python()

    assert gefunden == TRAINER_PYTHON
    assert gefunden != sys.executable


def test_ohne_umgebungsvariable_gibt_es_keine_trainer_wurzel():
    with pytest.raises(LoraError) as fehler:
        finde_trainer_wurzel(hole_trainer("kohya"))

    assert lora.UMGEBUNG_TRAINER_WURZEL in str(fehler.value)
    assert "kohya" in str(fehler.value)


# --------------------------------------------------------------------------------------
# C2 · baue_kommando — prüfbar ohne GPU, das ist der ganze Sinn der Bauform
# --------------------------------------------------------------------------------------

def test_kommando_ruft_das_fremde_venv_mit_dem_trainerskript(trainer_umgebung):
    """Regel 2/4 im Vollzug: fremdes Python, fremdes Skript, eigener Prozess."""
    cmd = baue_kommando(auftrag())

    assert cmd[0] == TRAINER_PYTHON
    assert cmd[1] == str(Path(TRAINER_WURZEL) / TRAINER["kohya"].skript)


def test_kommando_traegt_alle_parameter_mit_den_flaggen_der_registry(trainer_umgebung):
    """Die Flaggennamen stehen in der Registry, nicht im Code — und nicht doppelt im Test."""
    a = auftrag(rang=32, schritte=800, lernrate=5e-5, aufloesung=768, seed=99)
    f = TRAINER["kohya"].flaggen

    cmd = baue_kommando(a, modell_wurzel=f"/ai/attrappe/{a.basis}")

    assert cmd[cmd.index(f["basis"]) + 1] == f"/ai/attrappe/{a.basis}"
    assert cmd[cmd.index(f["datensatz"]) + 1] == DATENSATZ_AUSSERHALB
    assert cmd[cmd.index(f["ausgabe"]) + 1] == AUSGABE_AUSSERHALB
    assert cmd[cmd.index(f["rang"]) + 1] == "32"
    assert cmd[cmd.index(f["schritte"]) + 1] == "800"
    assert cmd[cmd.index(f["lernrate"]) + 1] == "5e-05"
    assert cmd[cmd.index(f["seed"]) + 1] == "99"


def test_aufloesung_wird_als_paar_uebergeben(trainer_umgebung):
    """kohya erwartet ``breite,hoehe`` — eine einzelne Zahl wäre eine andere Angabe."""
    cmd = baue_kommando(auftrag(aufloesung=768))
    assert cmd[cmd.index(TRAINER["kohya"].flaggen["aufloesung"]) + 1] == "768,768"


def test_zusatzflaggen_stehen_am_ende(trainer_umgebung):
    """Am Ende, damit sie die gebauten Flaggen überschreiben können — siehe Befund unten."""
    cmd = baue_kommando(auftrag(zusatzflaggen=("--xformers", "--cache_latents")))
    assert cmd[-2:] == ["--xformers", "--cache_latents"]


def test_ohne_angabe_kommt_die_modellwurzel_aus_render(monkeypatch, trainer_umgebung):
    """Wo die Gewichte liegen, weiss ``render`` — an EINER Stelle, nicht an zweien."""
    monkeypatch.setenv(render.UMGEBUNG_MODELLE, "/woanders/modelle")

    cmd = baue_kommando(auftrag(basis="qwen-image-2512"))

    assert cmd[cmd.index("--pretrained_model_name_or_path") + 1] == \
        "/woanders/modelle/qwen-image-2512"


def test_ai_toolkit_verweigert_die_auskunft_statt_eine_zeile_zu_erfinden(trainer_umgebung):
    """Absicht, kein Loch: ai-toolkit wird über YAML gesteuert, ``flaggen`` ist leer.

    Eine erfundene Kommandozeile wäre schlimmer als eine ehrliche Absage — sie liefe
    durch, schlüge auf der HomeStation fehl und niemand wüsste, warum. Dieselbe Haltung
    wie beim ``beleg``-Feld: Übernommenes wird nicht als Geprüftes ausgegeben.
    """
    with pytest.raises(LoraError) as fehler:
        baue_kommando(auftrag(trainer="ai-toolkit"))

    meldung = str(fehler.value)
    assert "ai-toolkit" in meldung
    assert "Konfigurationsdatei" in meldung
    assert "erfindet" in meldung


def test_ai_toolkit_startet_auch_ueber_trainiere_nichts(trainer_umgebung):
    """Der Umweg über ``trainiere`` führt zur selben Absage — und zu keinem Prozess."""
    attrappe = Attrappe()

    ergebnis = trainiere(auftrag(trainer="ai-toolkit"), _starte=attrappe)

    assert ergebnis["status"] == "abgelehnt"
    assert attrappe.wurde_gerufen is False


def test_unbekannter_trainer_wird_gemeldet_und_nennt_die_bekannten():
    with pytest.raises(LoraError) as fehler:
        hole_trainer("kohya-ss")

    assert "kohya" in str(fehler.value) and "ai-toolkit" in str(fehler.value)


def test_unbekannter_trainer_ist_ein_mangel_kein_absturz():
    """Im Auftrag wird daraus ein Mangel — ``pruefe_auftrag`` sammelt, statt zu werfen."""
    maengel = pruefe_auftrag(auftrag(trainer="kohya-ss"))
    assert any("Unbekannter Trainer" in m for m in maengel)


def test_ohne_trainer_umgebung_wird_abgelehnt_statt_gerechnet():
    """Fehlt das venv, entsteht gar kein Kommando — und schon gar kein Prozess."""
    attrappe = Attrappe()

    ergebnis = trainiere(auftrag(), _starte=attrappe)

    assert ergebnis["status"] == "abgelehnt"
    assert attrappe.wurde_gerufen is False
    assert any(lora.UMGEBUNG_TRAINER_PYTHON in m for m in ergebnis["maengel"])


# --------------------------------------------------------------------------------------
# C3 · trainiere — nachsehen statt behaupten
# --------------------------------------------------------------------------------------

def test_vollstaendiger_durchlauf_liefert_ok_und_einen_pfad(tmp_path, trainer_umgebung):
    """Ohne GPU, ohne Trainer, ohne Gewichte: die Verdrahtung geht durch."""
    ziel = tmp_path / "lora"
    attrappe = Attrappe(nebenwirkung=legt_lora_ab("haus-stil.safetensors"))

    ergebnis = trainiere(auftrag(ausgabe=str(ziel)), _starte=attrappe)

    assert ergebnis["status"] == "ok"
    assert ergebnis["lora"] == str(ziel / "haus-stil.safetensors")
    assert Path(ergebnis["lora"]).is_file()
    assert ergebnis["error"] is None
    assert ergebnis["lizenz"]["verkaufbar"] is True


def test_ergebnis_traegt_die_vertragsfelder(tmp_path, trainer_umgebung):
    """Der Ergebnissatz ist im Docstring zugesagt — er wird hier abgezählt."""
    ergebnis = trainiere(auftrag(ausgabe=str(tmp_path / "lora")),
                         _starte=Attrappe(nebenwirkung=legt_lora_ab()))

    for feld in ("status", "lora", "lizenz", "parameter", "maengel", "hinweise", "error"):
        assert feld in ergebnis, f"Pflichtfeld {feld} fehlt im Ergebnis"


def test_parameter_enthalten_alles_zur_wiederholung(tmp_path, trainer_umgebung):
    """Ohne vollständige Wiederholvorschrift liesse sich ein Stilunterschied nicht zuordnen."""
    ergebnis = trainiere(auftrag(ausgabe=str(tmp_path / "l"), rang=8, schritte=200,
                                 lernrate=2e-4, aufloesung=512, seed=7),
                         _starte=Attrappe(nebenwirkung=legt_lora_ab()))

    assert ergebnis["parameter"] == {
        "basis": backbone.VORGABE_BACKBONE, "trainer": VORGABE_TRAINER, "rang": 8,
        "schritte": 200, "lernrate": 2e-4, "aufloesung": 512, "seed": 7,
    }


def test_null_ohne_datei_ist_ein_fehlschlag(tmp_path, trainer_umgebung):
    """Die Lehre, die dieses Projekt schon zweimal bezahlt hat.

    Ein Trainer, der 0 meldet und nichts hinterlässt, ist gescheitert. Die Existenz
    eines Rückgabewerts ist kein Beleg für eine Datei — dieselbe Nachprüfung wie in
    ``render.rendere`` und ``seams.glb_zu_tiefenkarte``.
    """
    ziel = tmp_path / "lora"
    ziel.mkdir()
    attrappe = Attrappe(Ergebnis(returncode=0))

    ergebnis = trainiere(auftrag(ausgabe=str(ziel)), _starte=attrappe)

    assert attrappe.wurde_gerufen is True, "Vorbedingung: der Lauf hat stattgefunden"
    assert ergebnis["status"] == "fehler"
    assert ergebnis["lora"] is None
    assert "safetensors" in ergebnis["error"]


def test_null_ohne_verzeichnis_ist_ebenfalls_ein_fehlschlag(tmp_path, trainer_umgebung):
    """Auch das gar nicht angelegte Ausgabeverzeichnis darf nicht als Erfolg durchgehen."""
    ergebnis = trainiere(auftrag(ausgabe=str(tmp_path / "nie-angelegt")),
                         _starte=Attrappe(Ergebnis(returncode=0)))

    assert ergebnis["status"] == "fehler"


def test_datei_mit_falscher_endung_gilt_nicht(tmp_path, trainer_umgebung):
    """Gegenprobe zur Nachschau: Irgendeine Datei genügt nicht, es muss die richtige sein."""
    def legt_falsches_ab(cmd):
        ziel = Path(cmd[cmd.index("--output_dir") + 1])
        ziel.mkdir(parents=True, exist_ok=True)
        (ziel / "protokoll.txt").write_text("fertig", encoding="utf-8")

    ergebnis = trainiere(auftrag(ausgabe=str(tmp_path / "lora")),
                         _starte=Attrappe(nebenwirkung=legt_falsches_ab))

    assert ergebnis["status"] == "fehler"


def test_rueckgabewert_ungleich_null_wird_gemeldet(tmp_path, trainer_umgebung):
    """Die Meldung des Trainers wird durchgereicht, nicht verschluckt."""
    attrappe = Attrappe(Ergebnis(returncode=1, stderr="CUDA out of memory"))

    ergebnis = trainiere(auftrag(ausgabe=str(tmp_path / "lora")), _starte=attrappe)

    assert ergebnis["status"] == "fehler"
    assert "CUDA out of memory" in ergebnis["error"]
    assert ergebnis["lora"] is None


def test_bei_stiller_stderr_wird_stdout_gemeldet(tmp_path, trainer_umgebung):
    """Manche Trainer schreiben ihren Abbruch nach stdout — verloren gehen darf er nicht."""
    ergebnis = trainiere(auftrag(ausgabe=str(tmp_path / "l")),
                         _starte=Attrappe(Ergebnis(returncode=2, stdout="Abbruch: OOM")))
    assert "Abbruch: OOM" in ergebnis["error"]


def test_timeout_hat_die_vorgabe_von_24_stunden(tmp_path, trainer_umgebung):
    """Ein Stiltraining ist das Längste, was diese Kette tut — ein knapper Wert bräche es ab."""
    attrappe = Attrappe(nebenwirkung=legt_lora_ab())

    trainiere(auftrag(ausgabe=str(tmp_path / "lora")), _starte=attrappe)

    assert attrappe.timeouts == [86400]


def test_timeout_wird_durchgereicht(tmp_path, trainer_umgebung):
    """Der Wert des Aufrufers muss an der Naht ankommen, nicht in ``trainiere`` versanden."""
    attrappe = Attrappe(nebenwirkung=legt_lora_ab())

    trainiere(auftrag(ausgabe=str(tmp_path / "lora")), timeout=42, _starte=attrappe)

    assert attrappe.timeouts == [42]


def test_der_trainer_wird_genau_einmal_gerufen(tmp_path, trainer_umgebung):
    attrappe = Attrappe(nebenwirkung=legt_lora_ab())
    trainiere(auftrag(ausgabe=str(tmp_path / "lora")), _starte=attrappe)
    assert len(attrappe.kommandos) == 1


def test_mehrere_ergebnisse_werden_stabil_ausgewaehlt(tmp_path, trainer_umgebung):
    """kohya legt Zwischenstände ab. Gewählt wird der letzte in sortierter Reihenfolge —
    festgehalten, damit ein Wechsel der Auswahl auffällt statt still zu passieren."""
    def legt_mehrere_ab(cmd):
        ziel = Path(cmd[cmd.index("--output_dir") + 1])
        ziel.mkdir(parents=True, exist_ok=True)
        for name in ("stil-000001.safetensors", "stil-000002.safetensors"):
            (ziel / name).write_bytes(b"x")

    ergebnis = trainiere(auftrag(ausgabe=str(tmp_path / "lora")),
                         _starte=Attrappe(nebenwirkung=legt_mehrere_ab))

    assert ergebnis["status"] == "ok"
    assert ergebnis["lora"].endswith("stil-000002.safetensors")


# ======================================================================================
# D · DIE TRAINER-REGISTRY — permissiv, belegt, und ehrlich über das Nichtgemessene
# ======================================================================================

def test_beide_trainer_sind_vorhanden():
    assert set(TRAINER) == {"kohya", "ai-toolkit"}
    assert VORGABE_TRAINER in TRAINER


@pytest.mark.parametrize("name", sorted(TRAINER))
def test_jeder_trainer_ist_permissiv_lizenziert(name):
    """Regel 1 gilt auch für das Werkzeug, nicht nur für die Gewichte."""
    assert lizenzquelle.ist_permissiv(TRAINER[name].lizenz), \
        f"{name}: '{TRAINER[name].lizenz}' ist keine der vier Lizenzen aus Regel 1"


def test_die_erwarteten_lizenzen_stehen_da():
    """Namentlich, damit ein stiller Wechsel im Eintrag auffällt."""
    assert TRAINER["kohya"].lizenz == "Apache-2.0"
    assert TRAINER["ai-toolkit"].lizenz == "MIT"


@pytest.mark.parametrize("name", sorted(TRAINER))
def test_jede_lizenzangabe_ist_belegt(name):
    """Ein Vermerk, den die Prüflogik nicht als Beleg erkennt, ist kein Beleg.

    Genau daran ist die Lizenzprüfung vom 18.08.2026 hängengeblieben — darum wird hier
    gegen ``lizenzquelle.ist_belegt`` geprüft und nicht auf das Wort „geprüft" gesucht.
    """
    assert lizenzquelle.ist_belegt(TRAINER[name].lizenz_quelle) is True
    assert lizenzquelle.hinweis_zur_herkunft(TRAINER[name].lizenz_quelle) is None


@pytest.mark.parametrize("name", sorted(TRAINER))
def test_jeder_eintrag_hat_einen_beleg_der_die_quelle_nennt(name):
    """Nichtleer, und er sagt, dass die Lizenz **am Original** gelesen wurde."""
    beleg = TRAINER[name].beleg

    assert beleg.strip()
    assert "Lizenz am Original gelesen" in beleg


def test_der_beleg_trennt_geprueftes_von_uebernommenem():
    """Die Lizenz ist gelesen, die Kommandozeile ist abgeschrieben — beides steht getrennt da.

    „Beides in einem Feld zu führen wäre die Art Ungenauigkeit, die dieses Projekt schon
    zweimal Geld gekostet hat" (Docstring von ``Trainer``). Der kohya-Eintrag ist der
    einzige mit Flaggen und muss den Vorbehalt darum ausdrücklich tragen.
    """
    beleg = TRAINER["kohya"].beleg

    assert "Projektdokumentation" in beleg
    assert "NIE ausgeführt" in beleg
    assert "weder GPU noch Trainer" in beleg


def test_der_beleg_von_ai_toolkit_begruendet_die_leeren_flaggen():
    """Leere Flaggen sind hier eine Aussage, kein vergessenes Feld — das steht dabei."""
    eintrag = TRAINER["ai-toolkit"]

    assert eintrag.flaggen == {}
    assert "YAML" in eintrag.beleg
    assert "verweigert" in eintrag.beleg


def test_kohya_traegt_jede_flagge_die_das_kommando_braucht():
    """Fehlte eine, bräche ``baue_kommando`` mit einem ``KeyError`` statt mit einer Meldung."""
    erwartet = {"basis", "datensatz", "ausgabe", "rang", "schritte", "lernrate",
                "aufloesung", "seed"}
    assert erwartet <= set(TRAINER["kohya"].flaggen)


@pytest.mark.parametrize("name", sorted(TRAINER))
def test_trainer_eintraege_sind_unveraenderlich(name):
    """``frozen=True``: Die Lizenzangabe soll nicht an einer beliebigen Stelle kippbar sein."""
    with pytest.raises(Exception):
        TRAINER[name].lizenz = "GPL-3.0"


# ======================================================================================
# E · PARAMETERPRÜFUNG — laut, vollständig, und nie zurechtgebogen
# ======================================================================================

def test_gueltiger_auftrag_hat_keine_maengel():
    assert pruefe_auftrag(auftrag()) == []


@pytest.mark.parametrize("feld, unten", [("rang", 1), ("schritte", 1), ("aufloesung", 64)])
@pytest.mark.parametrize("wert", [0, -1, 2.5, "16", None])
def test_ganze_zahlen_ab_einer_untergrenze(feld, unten, wert):
    """Unter der Grenze oder gar keine ganze Zahl — beides wird benannt, nichts geraten.

    Die fünf Werte sind für alle drei Felder ungültig; die Untergrenze selbst prüft der
    Test darunter. So bleibt hier jede Kombination eine echte Probe.
    """
    maengel = pruefe_auftrag(auftrag(**{feld: wert}))
    assert any(m.startswith(f"{feld}:") for m in maengel)


@pytest.mark.parametrize("feld", ["rang", "schritte", "aufloesung"])
def test_wahrheitswert_ist_keine_zahl(feld):
    """``True`` wäre 1 und liefe stillschweigend durch — als Rang ist es immer ein Irrtum."""
    maengel = pruefe_auftrag(auftrag(**{feld: True}))
    assert any(m.startswith(f"{feld}:") for m in maengel)


@pytest.mark.parametrize("feld, gerade_noch", [("rang", 1), ("schritte", 1),
                                               ("aufloesung", 64)])
def test_die_untergrenze_selbst_ist_erlaubt(feld, gerade_noch):
    """Gegenprobe: Die Grenze liegt dort, wo sie dokumentiert ist — nicht eins daneben."""
    assert pruefe_auftrag(auftrag(**{feld: gerade_noch})) == []
    assert any(m.startswith(f"{feld}:")
               for m in pruefe_auftrag(auftrag(**{feld: gerade_noch - 1})))


@pytest.mark.parametrize("lernrate", [0, 1, 1.5, -0.1, True, "1e-4", None])
def test_lernrate_liegt_echt_zwischen_null_und_eins(lernrate):
    """Beide Enden ausgeschlossen: 0 lernt nichts, 1 zerlegt das Modell."""
    maengel = pruefe_auftrag(auftrag(lernrate=lernrate))
    assert any(m.startswith("lernrate:") for m in maengel)


@pytest.mark.parametrize("lernrate", [1e-4, 1e-5, 0.5])
def test_uebliche_lernraten_gehen_durch(lernrate):
    """Gegenprobe — sonst wäre der Test darüber auch grün, wenn alles abgelehnt würde."""
    assert pruefe_auftrag(auftrag(lernrate=lernrate)) == []


def test_die_meldung_zur_lernrate_nennt_die_ueblichen_werte():
    """Wer den Fehler macht, kennt den Zielbereich meist nicht — er steht in der Meldung."""
    (meldung,) = pruefe_auftrag(auftrag(lernrate=5))
    assert "1e-4" in meldung and "1e-5" in meldung


def test_drei_maengel_ergeben_drei_saetze():
    """``pruefe_auftrag`` bricht nicht beim ersten Fund ab — sonst scheitert man dreimal.

    Der Docstring sagt es ausdrücklich: „vollständig statt beim ersten Fund abbrechend".
    """
    maengel = pruefe_auftrag(auftrag(rang=0, schritte=-1, lernrate=9))

    assert len(maengel) == 3
    assert {m.split(":")[0] for m in maengel} == {"rang", "schritte", "lernrate"}


def test_alle_regeln_gleichzeitig_werden_alle_genannt():
    """Regel 1, zweimal Regel 3, unbekannter Trainer und eine Zahl — fünf Sätze, ein Durchgang."""
    maengel = pruefe_auftrag(LoraAuftrag(
        basis="flux1-dev", datensatz=str(REPO / "bilder"), ausgabe=str(REPO / "loras"),
        trainer="gibt-es-nicht", rang=0))

    assert len(maengel) == 5
    assert sum(m.startswith("REGEL 1") for m in maengel) == 1
    assert sum(m.startswith("REGEL 3") for m in maengel) == 2


def test_kein_auftrag_wirft_statt_zu_raten():
    """Ohne Auftrag gibt es keine Parameter — und damit kein protokollierbares Ergebnis."""
    with pytest.raises(LoraError, match="LoraAuftrag"):
        pruefe_auftrag({"basis": "qwen-image-edit-2511"})


def test_der_auftrag_ist_unveraenderlich():
    """``frozen=True``: Ein Auftrag ist das Protokoll dessen, was gerechnet wurde."""
    a = auftrag()
    with pytest.raises(Exception):
        a.basis = "flux1-dev"


def test_die_vorgaben_ergeben_fuer_sich_genommen_einen_gueltigen_auftrag():
    """Wer nur die drei Pflichtfelder setzt, bekommt keinen Mängelbericht."""
    a = LoraAuftrag(basis=backbone.VORGABE_BACKBONE, datensatz=DATENSATZ_AUSSERHALB,
                    ausgabe=AUSGABE_AUSSERHALB)

    assert (a.trainer, a.rang, a.schritte, a.aufloesung, a.seed) == \
        (VORGABE_TRAINER, 16, 1500, 1024, 0)
    assert pruefe_auftrag(a) == []


# ======================================================================================
# BEFUNDE — beobachtetes Verhalten, nicht gewünschtes
# ======================================================================================
#
# Die vier Tests hier halten Stellen fest, an denen das Modul weniger zusichert, als man
# ihm beim Lesen des Modulkopfs zutraut. Sie sind bewusst als *Beschreibung* geschrieben
# und nicht als Forderung: Ob und wie sie geschlossen werden, ist ein Entscheid und keine
# Aufräumarbeit — dieselbe Haltung wie bei `lizenzquelle.regel_1_spannung`. Ändert sich
# das Verhalten, wird hier rot, und der Entscheid ist sichtbar gefallen.

def test_modell_wurzel_wird_gegen_die_basis_geprueft(trainer_umgebung):
    """**Das grösste Loch in der Ausführbarkeit von Regel 1 — geschlossen am 18.08.2026.**

    ``lizenz_des_ergebnisses`` urteilt über den **Namen** ``basis``. ``modell_wurzel``
    zeigt aber auf die tatsächlichen Gewichte, und bis zur Testabnahme wurde sie nirgends
    dagegen gehalten. Wer ``basis='qwen-image-edit-2511'`` schrieb und ``modell_wurzel``
    auf FLUX-dev richtete, bekam eine vollständige Kommandozeile — und ein Ergebnis, das
    sich als verkaufbar auswies, ohne es zu sein.

    Regel 1 war damit gegen das Versehen abgesichert, aber nicht gegen jemanden, der
    ``modell_wurzel`` kennt.

    **Die Grenze der Behebung gehört in denselben Test**, damit niemand sie für mehr
    hält, als sie ist: Es ist eine **Namensprüfung, keine Inhaltsprüfung**. Wer ein
    FLUX-Verzeichnis in ``qwen-image-edit-2511`` umbenennt, kommt weiterhin durch.
    """
    with pytest.raises(LoraError) as fehler:
        baue_kommando(auftrag(), modell_wurzel="/ai/flux1-dev")

    text = str(fehler.value)
    assert "REGEL 1" in text
    assert "flux1-dev" in text and backbone.VORGABE_BACKBONE in text
    assert "Namensprüfung" in text, "die Grenze der Prüfung gehört in die Meldung"

    # Gegenprobe: Eine passende Wurzel geht durch. Ohne sie wäre der Test auch grün,
    # wenn die Prüfung schlicht jede Wurzel abwiese.
    passend = baue_kommando(auftrag(), modell_wurzel=f"/ai/{backbone.VORGABE_BACKBONE}")
    assert passend[passend.index("--pretrained_model_name_or_path") + 1] \
        == f"/ai/{backbone.VORGABE_BACKBONE}"


def test_die_namenspruefung_gibt_sich_nicht_fuer_eine_inhaltspruefung_aus(trainer_umgebung):
    """Die bekannte Restlücke, ausdrücklich festgehalten statt verschwiegen.

    Ein umbenanntes Verzeichnis kommt durch. Das ist kein Versäumnis, sondern die Grenze
    dessen, was ohne Lesen der Gewichte geht — und eine Prüfung, deren Grenze niemand
    kennt, wird für mehr gehalten, als sie ist.
    """
    assert pruefe_modell_wurzel(backbone.VORGABE_BACKBONE,
                                f"/tmp/irgendwo/{backbone.VORGABE_BACKBONE}") is None


def test_zusatzflaggen_duerfen_die_grundlage_nicht_ueberschreiben(trainer_umgebung):
    """**Derselbe Ausgang wie Befund 1, ohne ``modell_wurzel`` zu berühren — behoben.**

    ``zusatzflaggen`` wurde ungeprüft ans Ende gehängt. Bei einer Kommandozeile auf
    ``argparse``-Grundlage gewinnt die spätere Angabe; dieselbe Flagge stand dann zweimal
    im Kommando, und die zweite entschied. Damit liess sich an jeder Prüfung dieses
    Moduls vorbeitrainieren.

    Ob kohya die spätere Angabe wirklich vorzieht, ist hier **nicht messbar** — dieses
    Environment hat weder GPU noch Trainer, genau wie der ``beleg`` des Eintrags sagt.
    Aber eine Flagge, die diese Naht selbst vergibt, ein zweites Mal zuzulassen, ist auch
    ohne Messung falsch: Der Auftrag im Protokoll sagte dann etwas anderes als das
    Kommando.
    """
    maengel = pruefe_auftrag(auftrag(zusatzflaggen=("--pretrained_model_name_or_path",
                                                    "/ai/flux1-dev")))

    assert any("--pretrained_model_name_or_path" in m for m in maengel)
    assert any("Lizenzprüfung umgehen" in m for m in maengel)

    # Gegenprobe: Eine Flagge, die diese Naht NICHT vergibt, bleibt erlaubt — sonst wäre
    # `zusatzflaggen` als Feld sinnlos.
    assert pruefe_auftrag(auftrag(zusatzflaggen=("--mixed_precision", "bf16"))) == []


def test_ein_unbrauchbarer_pfad_ergibt_einen_mangel_statt_einer_ausnahme(trainer_umgebung):
    """``pruefe_auftrag`` sagt eine **Mängelliste** zu — auch für Unsinn.

    Bis zur Testabnahme flog bei ``datensatz=None`` ein ``TypeError`` aus ``Path()``
    heraus, statt dass die Liste geliefert wurde. Ein Aufrufer, der wie zugesagt auf
    Mängel prüft, bekam einen Absturz.
    """
    for wert in (None, "", "   ", 42):
        maengel = pruefe_auftrag(auftrag(datensatz=wert))
        assert any("datensatz" in m for m in maengel), f"kein Mangel für {wert!r}"

