"""Berührt eine spätere Änderung eine veröffentlichte Messung?

Der Anlass steht in `src/aiimaging/beruehrung.py`: Am 01.09.2026 hat eine Änderung an
`kameras.py` sieben veröffentlichte Dokumente entwertet, und acht Tage lang hat niemand
danach gefragt — weil es nichts gab, wonach man hätte fragen können.

Die Proben hier fahren gegen ein **echtes, synthetisches git-Repo** (Regel 3: erzeugt,
nicht abgelegt). Ein Test, der `git` wegmockt, prüfte am Ende die Attrappe: Ob
`git diff --name-only A..B -- src/aiimaging` das Richtige liefert, ist genau die Frage.
"""
from __future__ import annotations

import subprocess

import pytest

from aiimaging import beruehrung as ber
from aiimaging import messstand


def _git(repo, *args) -> str:
    lauf = subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True, check=True)
    return lauf.stdout.strip()


@pytest.fixture()
def repo(tmp_path):
    """Ein Repo mit drei Ständen: leer → `kameras.py` → `maske.py`."""
    _git(tmp_path, "init", "-q", "-b", "haupt")
    _git(tmp_path, "config", "user.email", "probe@example.invalid")
    _git(tmp_path, "config", "user.name", "Probe")
    kern = tmp_path / "src" / "aiimaging"
    kern.mkdir(parents=True)
    (kern / "__init__.py").write_text("", encoding="utf-8")
    (kern / "kameras.py").write_text("ABSTAND = 1.0\n", encoding="utf-8")
    (kern / "maske.py").write_text("SCHWELLE = 0.25\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "Anfang")
    # Der Stand wird in eine Datei geschrieben statt an das Path-Objekt gehängt: An ein
    # `PosixPath` lässt sich nichts anheften, und ein zweiter Rückgabewert machte jeden
    # Test hier um eine Zeile Auspacken länger.
    (tmp_path / ".probe-stand-null").write_text(
        _git(tmp_path, "rev-parse", "HEAD"), encoding="utf-8")

    (kern / "kameras.py").write_text("ABSTAND = 0.76\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "Kameraabstand verkuerzt")
    return tmp_path


def _null(repo) -> str:
    """Der erste Stand des Probe-Repos."""
    return (repo / ".probe-stand-null").read_text(encoding="utf-8").strip()


def _dokument(repo, name, *, stand=None, grundlage=None) -> "Path":
    docs = repo / "docs"
    docs.mkdir(exist_ok=True)
    zeilen = ["# Probe", ""]
    if stand:
        zeilen.append(f"{messstand.MARKE} `{stand}`")
    if grundlage:
        zeilen.append(f"{ber.MARKE_GRUNDLAGE} {grundlage}")
    zeilen += ["", "Score 0,712."]
    pfad = docs / name
    pfad.write_text("\n".join(zeilen) + "\n", encoding="utf-8")
    return pfad


def test_der_fall_vom_ersten_september(repo):
    """Genau der Vorgang, der das Modul ausgelöst hat: `kameras` hat sich bewegt."""
    doku = _dokument(repo, "MESSUNG_2026-09-09.md",
                     stand=_null(repo), grundlage="`kameras`, `maske`")

    satz = ber.beruehrung(doku, repo=repo)

    assert satz["zustand"] == ber.BERUEHRT
    assert satz["betroffen"] == ["kameras"]
    assert "kameras" in satz["grund"]


def test_wer_sich_auf_etwas_anderes_beruft_bleibt_unberuehrt(repo):
    doku = _dokument(repo, "MESSUNG_2026-09-09.md",
                     stand=_null(repo), grundlage="`maske`")

    satz = ber.beruehrung(doku, repo=repo)

    assert satz["zustand"] == ber.UNBERUEHRT
    assert satz["betroffen"] == []
    # Der Vorbehalt gehört an die Antwort, nicht in eine Fussnote.
    assert "Angabe, keine Messung" in satz["grund"]


def test_ohne_grundlage_gilt_nichts_als_unberuehrt(repo):
    """Der Kern des Moduls: Wer nichts angibt, bekommt kein «alles in Ordnung».

    Ein Werkzeug, das Schweigen als Entwarnung liest, ist schlimmer als keines — es
    erzeugt genau das Vertrauen, das es nicht rechtfertigen kann.
    """
    doku = _dokument(repo, "MESSUNG_2026-09-09.md", stand=_null(repo))

    satz = ber.beruehrung(doku, repo=repo)

    assert satz["zustand"] == ber.UNKLAR
    assert satz["geaendert"] == ["kameras"]
    assert "nicht «unberührt»" in satz["grund"]


def test_keine_ist_eine_angabe(repo):
    """`**Grundlage:** keine` ist etwas anderes als eine fehlende Zeile."""
    doku = _dokument(repo, "DURCHSICHT_2026-09-09.md",
                     stand=_null(repo), grundlage="keine")

    satz = ber.beruehrung(doku, repo=repo)

    assert satz["zustand"] == ber.UNBERUEHRT
    assert satz["grundlage"] == []


def test_ein_unbekannter_stand_wird_gemeldet_und_nicht_geraten(repo):
    """Die dritte Antwort, an der Stelle, an der sie am meisten kostet.

    Eine leere Änderungsliste hiesse «nichts hat sich bewegt». Auf «diesen Commit kenne
    ich nicht» ist das die falscheste aller möglichen Antworten.
    """
    doku = _dokument(repo, "MESSUNG_2026-09-09.md",
                     stand="0" * 40, grundlage="`kameras`")

    satz = ber.beruehrung(doku, repo=repo)

    assert satz["zustand"] == ber.UNKLAR
    assert "nicht auffindbar" in satz["grund"]
    with pytest.raises(ber.BeruehrungError, match="nicht auffindbar"):
        ber.geaenderte_module("0" * 40, "HEAD", repo)


def test_aenderungen_ausserhalb_des_kerns_beruehren_keine_messung(repo):
    """Ein Werkzeug, ein Dokument, eine Probe ändern nicht, was gerechnet wird."""
    (repo / "tools").mkdir(exist_ok=True)
    (repo / "tools" / "irgendwas.py").write_text("print(1)\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Werkzeug")

    assert ber.geaenderte_module(_null(repo), "HEAD", repo) == ["kameras"]


def test_die_durchsicht_stellt_das_beruehrte_nach_oben(repo):
    _dokument(repo, "A_2026-09-09.md", stand=_null(repo), grundlage="`maske`")
    _dokument(repo, "B_2026-09-09.md", stand=_null(repo))
    _dokument(repo, "C_2026-09-09.md", stand=_null(repo), grundlage="`kameras`")
    _dokument(repo, "D_2026-09-09.md")          # ohne Codestand — gehört nicht hinein

    reihe = ber.durchsicht(repo / "docs", repo=repo)

    assert [s["datei"] for s in reihe] == ["C_2026-09-09.md", "B_2026-09-09.md",
                                           "A_2026-09-09.md"]


def test_mutationsprobe_ohne_schnittmenge_faellt_der_wachter(repo, monkeypatch):
    """Ein Wächter, der nicht fällt, bewacht nichts.

    Meldet `geaenderte_module` nie etwas, muss der berührte Fall als unberührt
    durchgehen. Tut er es nicht, prüft der erste Test etwas anderes als das, was er
    zu prüfen vorgibt.
    """
    monkeypatch.setattr(ber, "geaenderte_module", lambda *a, **k: [])
    doku = _dokument(repo, "MESSUNG_2026-09-09.md",
                     stand=_null(repo), grundlage="`kameras`")

    assert ber.beruehrung(doku, repo=repo)["zustand"] == ber.UNBERUEHRT


# ── Die Durchsicht wird vermerkt, sonst ruft der Wächter ewig ─────────────────────────

def test_wer_nachgesehen_hat_wird_nicht_weiter_gemeldet(repo):
    """Der erste echte Fall: Die Änderung berührte das Modul, nicht die Zahl.

    `seams` hatte sich am 09.09.2026 geändert — an der Anlauffrist einer Prozesswache,
    also an etwas, das nicht ändert, was gerechnet wird. Ohne einen Vermerk stünde das
    Dokument bis in alle Ewigkeit auf «ansehen», und *ein Wächter, der nach der Klärung
    weiterruft, wird abgestellt.*
    """
    kopf = _git(repo, "rev-parse", "HEAD")
    doku = _dokument(repo, "MESSUNG_2026-09-09.md",
                     stand=_null(repo), grundlage="`kameras`")
    text = doku.read_text(encoding="utf-8")
    doku.write_text(text.replace(f"{ber.MARKE_GRUNDLAGE} `kameras`",
                                 f"{ber.MARKE_GRUNDLAGE} `kameras`\n"
                                 f"{ber.MARKE_NACHGESEHEN} `{kopf}`"), encoding="utf-8")

    satz = ber.beruehrung(doku, repo=repo)

    assert satz["zustand"] == ber.UNBERUEHRT
    assert satz["nachgesehen"] == kopf
    assert satz["von"] == kopf
    assert "nachgesehen bis" in satz["grund"]


def test_der_vermerk_deckt_nur_bis_wohin_er_reicht(repo):
    """Die Gegenprobe: Nach dem Vermerk ändert sich dasselbe Modul noch einmal."""
    kopf = _git(repo, "rev-parse", "HEAD")
    (repo / "src" / "aiimaging" / "kameras.py").write_text("ABSTAND = 0.5\n",
                                                           encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Noch einmal")
    doku = _dokument(repo, "MESSUNG_2026-09-09.md", stand=_null(repo),
                     grundlage="`kameras`")
    text = doku.read_text(encoding="utf-8")
    doku.write_text(text + f"\n{ber.MARKE_NACHGESEHEN} `{kopf}`\n", encoding="utf-8")

    assert ber.beruehrung(doku, repo=repo)["zustand"] == ber.BERUEHRT


# ── Der Wächter über die Grundlagenzeile ─────────────────────────────────────────────

def test_jedes_messdokument_ab_dem_stichtag_nennt_seine_grundlage():
    """Der Riegel, und er gilt für die Dokumente dieses Repos."""
    from pathlib import Path as _P
    wurzel = _P(__file__).resolve().parents[1]

    fehlend = ber.ohne_grundlage(wurzel / "docs")

    assert not fehlend, (
        f"{len(fehlend)} Dokument(e) ohne Grundlagenzeile: {fehlend}. Eine Messung, die "
        f"nicht sagt, worauf sie steht, lässt sich nicht benachrichtigen, wenn ihr Boden "
        f"sich bewegt.")


def test_aeltere_dokumente_muessen_ihre_grundlage_nicht_nachtragen(tmp_path):
    """Dieselbe Zurückhaltung wie beim Codestand — und aus demselben Grund.

    Welche Module eine Messung vom 20.08.2026 trägt, liesse sich nur vermuten. *Eine Regel
    rückwirkend mit Vermutungen zu erfüllen ist schlimmer, als sie erst ab morgen zu
    haben.*
    """
    (tmp_path / "ALT_2026-08-20.md").write_text("# Alt\n\nZahlen.\n", encoding="utf-8")

    assert ber.ohne_grundlage(tmp_path) == []


def test_ein_dokument_ab_dem_stichtag_ohne_grundlage_faellt_auf(tmp_path):
    """Die Gegenprobe: Ohne sie prüfte der Riegel nur, dass eine Liste leer bleibt."""
    (tmp_path / "NEU_2026-09-11.md").write_text(
        f"# Neu\n\n{messstand.MARKE} `abc1234`\n", encoding="utf-8")

    assert ber.ohne_grundlage(tmp_path) == ["NEU_2026-09-11.md"]


# ── Das Werkzeug: jeder Schalter wird einmal gedrückt ────────────────────────────────
#
# `tests/test_schalterprobe.py` verlangt das, und zu Recht: Am 01.09.2026 waren zwei von
# neun ungedrückten Schaltern schlicht kaputt. Ein Schalter ohne Wirkung sagt, etwas sei
# geschehen.

def _werkzeug():
    import importlib.util
    from pathlib import Path as _P
    pfad = _P(__file__).resolve().parents[1] / "tools" / "beruehrung.py"
    spec = importlib.util.spec_from_file_location("werkzeug_beruehrung", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_werkzeug_meldet_das_beruehrte_und_gibt_eins_zurueck(repo, capsys):
    _dokument(repo, "MESSUNG_2026-09-09.md", stand=_null(repo), grundlage="`kameras`")

    rueckgabe = _werkzeug().main(["--repo", str(repo), "--docs", "docs"])

    assert rueckgabe == 1
    assert "ANSEHEN" in capsys.readouterr().out


def test_werkzeug_nur_beruehrt_laesst_das_ruhige_weg(repo, capsys):
    _dokument(repo, "RUHIG_2026-09-09.md", stand=_null(repo), grundlage="`maske`")
    _dokument(repo, "LAUT_2026-09-09.md", stand=_null(repo), grundlage="`kameras`")

    _werkzeug().main(["--repo", str(repo), "--nur-beruehrt"])
    ausgabe = capsys.readouterr().out

    assert "LAUT_2026-09-09.md" in ausgabe
    assert "RUHIG_2026-09-09.md" not in ausgabe


def test_werkzeug_bis_vergleicht_gegen_einen_anderen_endstand(repo, capsys):
    """`--bis` gegen den Anfangsstand selbst: dieselbe Strecke, Länge null."""
    _dokument(repo, "MESSUNG_2026-09-09.md", stand=_null(repo), grundlage="`kameras`")

    rueckgabe = _werkzeug().main(["--repo", str(repo), "--bis", _null(repo)])

    assert rueckgabe == 0
    assert "ruhig" in capsys.readouterr().out


# ── Der Bericht zaehlt es mit ────────────────────────────────────────────────────────
#
# «Was von Hand gezaehlt wird, wird irgendwann nicht mehr gezaehlt» — dieselbe Begründung
# wie bei der Vergabestelle. Darum steht die Zahl dort, wo ohnehin gezählt wird.

def test_der_einbaubericht_meldet_beruehrte_messungen(repo):
    from aiimaging import einbau

    _dokument(repo, "MESSUNG_2026-09-09.md", stand=_null(repo), grundlage="`kameras`")

    befund = einbau._beruehrte_messungen(repo)

    assert [e["datei"] for e in befund["beruehrt"]] == ["MESSUNG_2026-09-09.md"]
    assert befund["beruehrt"][0]["betroffen"] == ["kameras"]


def test_das_unklare_wird_getrennt_gezaehlt_und_nicht_als_unberuehrt(tmp_path):
    """Die dritte Antwort, auf den Bericht angewandt.

    Ein Dokument, dessen Stand dieses Arbeitsverzeichnis nie gesehen hat, ist nicht
    «unberührt» — es ist unbeantwortbar. Nur die berührten zu melden hiesse, das Unklare
    stillschweigend zu den Ruhigen zu zählen.
    """
    from aiimaging import einbau

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "M_2026-09-09.md").write_text(
        f"# M\n\n{messstand.MARKE} `abc1234`\n", encoding="utf-8")

    befund = einbau._beruehrte_messungen(tmp_path)

    assert befund["beruehrt"] == []
    assert befund["beruehrt_unklar"] == ["M_2026-09-09.md"]


def test_ein_dokument_das_den_begriff_nur_erklaert_ist_kein_messdokument(repo):
    """Der Fehler, den der erste Entwurf gemacht hat — zweimal am selben Nachmittag.

    Das Lexikon **erklärt** die Marke und das Einbindungsblatt benutzt das Wort
    «Grundlage» im Fliesstext. Beide wurden als Messdokument gemeldet, weil die Marke
    irgendwo vorkam. *Ein Wächter, der auf ein Wort statt auf eine Sache prüft, prüft die
    Prosa.*
    """
    docs = repo / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "LEXIKON.md").write_text(
        f"# Lexikon\n\nSo sieht sie aus: `{messstand.MARKE} `abc1234``.\n",
        encoding="utf-8")
    (docs / "PROSA_2026-09-09.md").write_text(
        f"# Prosa\n\nDie {ber.MARKE_GRUNDLAGE} dieser Arbeit ist eine andere.\n",
        encoding="utf-8")
    _dokument(docs.parent, "ECHT_2026-09-09.md", stand=_null(repo), grundlage="`maske`")

    assert [s["datei"] for s in ber.durchsicht(docs, repo=repo)] == ["ECHT_2026-09-09.md"]
    assert ber.ohne_grundlage(docs) == []
