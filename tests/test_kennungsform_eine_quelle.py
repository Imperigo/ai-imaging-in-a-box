"""EINE QUELLE FÜR DIE FREMDE KENNUNGSFORM — und drei Stellen, die sie lesen.

Der Befund (22.09.2026)
-----------------------
Die Regel, wie ein Auftrag der fremden Warteschlange heisst (``vis-<zahl>-<6 hex>``),
stand **dreimal** im Repo, jedes Mal ausgeschrieben, und keine Stelle las eine andere:

* ``bruecke.VERZEICHNIS_MUSTER``      — filtert die Auftragsordner
* ``kosmo_szene.FREMDE_JOB_ID``       — prüft den Vertrag (``pruefe_job_id``)
* ``kosmo_naht.FREMDES_JOB_ID_MUSTER`` — eine Ausfuhr der Naht, **kein Weg**

Die dritte Stelle ist ehrlich gesagt keine: Im Produkt liest den Namen niemand, auch
``kosmo_naht`` selbst nicht. Zwei Stellen liegen auf einem Weg, die dritte ist eine
blosse Auskunft für Leser von aussen. Sie steht hier trotzdem mit, weil eine Auskunft,
die anders lautet als die Stelle, die entscheidet, genau so in die Irre führt.

Was das kostet, sobald die fremde Warteschlange ihre Kennungsform weitet: Geändert wird
die Stelle, an der der Vertrag geprüft wird. ``bruecke.offene_auftraege`` filtert danach
weiter mit dem alten Muster und überspringt den neuen Auftragsordner **stillschweigend**
— kein Fehler, keine Warnung, der Auftrag bleibt liegen, und niemand sieht etwas Rotes.

Was diese Wächter prüfen
------------------------
Nicht, dass irgendwo ein Bezeichner steht — das prüfte den Text und nicht das Programm.
Geprüft wird die **Wirkung**:

1. Ein Ordnername in neuer Form wird an allen drei Stellen **gleich** behandelt. Die
   Liste der Namen enthält ausdrücklich die Formen, die eine Weitung erzeugen würde
   (acht Hexziffern, Grossbuchstaben, ein Zusatzteil).
2. Wird die eine Quelle geändert, **ändert sich der Produktweg der Brücke mit** — der
   Weg, den ein Auftrag wirklich geht, nicht bloss der direkte Aufruf.
3. Die Regel kommt in ``src/aiimaging`` **genau einmal** als Wert vor — gleich, wie
   sie geschrieben ist (roh ``r"…"`` oder mit verdoppelten Rückstrichen). Das ist eine
   Prüfung auf die Abwesenheit einer zweiten Kopie — der einzige Fall, in dem ein
   Blick in den Quelltext ein Wächter sein darf.

Regel 3: alle Daten synthetisch, von Hand gebaut, nichts aus einem echten Projekt.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from aiimaging import bruecke, kosmo_naht, kosmo_szene


#: Ordnernamen, über die die drei Stellen **dasselbe** sagen müssen.
#:
#: Die Liste ist mit Absicht breiter als der heutige Vertrag: Ein Wächter, der nur die
#: heute gültige Form kennt, merkt eine Weitung an einer einzelnen Stelle nicht. Darum
#: stehen die plausiblen Weitungen mit darin — acht statt sechs Hexziffern,
#: Grossbuchstaben, ein angehängter Teil.
NAMEN = (
    "vis-1-abc123",                 # heute gültig, kürzest mögliche Zahl
    "vis-1755600000-0f9e2a",        # heute gültig, ihre Unix-Zeit
    "vis-20260922120000-0f9e2a",    # heute gültig, unsere vierzehnstellige Form
    "vis-1755600000-0f9e2ab7",      # acht Hexziffern — die naheliegendste Weitung
    "vis-1-ABC123",                 # Grossbuchstaben
    "vis-1-abc12",                  # fünf Hexziffern
    "vis-1755600000-0f9e2a-neu",    # ein Teil zuviel
    "vis-abc-123456",               # Buchstaben statt Zahl
    "vis--abc123",                  # leerer Zahlenteil
    "VIS-1-abc123",                 # anderer Vorsatz
    "job-1-abc123",                 # fremder Vorsatz
    "out",                          # ein gewöhnlicher Nachbarordner
)


def _lege_auftrag_an(store: Path, name: str) -> Path:
    """Ein Auftragsverzeichnis, wie die fremde Brücke es anlegt — synthetisch und knapp.

    Mehr als Laufzettel und Bestellung braucht es hier nicht: Geprüft wird, ob der
    Ordner **gefunden** wird, nicht, was in ihm steht.
    """
    d = store / name
    d.mkdir(parents=True)
    (d / bruecke.DATEI_SZENE).write_text(json.dumps({
        "schema": kosmo_szene.SCHEMA_SZENE,
        "geometry": {"path": str(d / bruecke.DATEI_MODELL), "format": "glb"},
    }), encoding="utf-8")
    (d / bruecke.DATEI_LAUFZETTEL).write_text(json.dumps({
        "job_id": name, "status": bruecke.STATUS_QUEUED,
        "approval_token": "CONFIRMED_RENDER_deadbeef",
    }), encoding="utf-8")
    return d


# --------------------------------------------------------------------------------------
# 1 · Dieselbe Auskunft an allen drei Stellen
# --------------------------------------------------------------------------------------

def test_ein_ordnername_wird_an_allen_drei_stellen_gleich_behandelt(tmp_path):
    """Der Produktweg der Brücke, der Vertragsprüfer und die Naht sagen dasselbe.

    Gemessen wird an der Wirkung: Für jeden Namen wird ein echtes Auftragsverzeichnis
    angelegt und ``offene_auftraege`` gefragt, ob es als Auftrag gilt. Daneben steht,
    was ``pruefe_job_id`` über dieselbe Kennung sagt und was die Naht meldet.

    Weicht eine der drei ab, ist die Regel wieder zweimal im Repo — und der Auftrag in
    der abweichenden Form bleibt an genau einer Stelle stillschweigend liegen.
    """
    store = tmp_path / "store"
    store.mkdir()
    for name in NAMEN:
        _lege_auftrag_an(store, name)

    gefunden = {p.name for p in bruecke.offene_auftraege(store)}

    abweichungen = []
    for name in NAMEN:
        urteile = {
            "bruecke.offene_auftraege": name in gefunden,
            "kosmo_szene.pruefe_job_id": kosmo_szene.pruefe_job_id(name)["passt"],
            "kosmo_naht.FREMDES_JOB_ID_MUSTER":
                kosmo_naht.FREMDES_JOB_ID_MUSTER.match(name) is not None,
        }
        if len(set(urteile.values())) != 1:
            abweichungen.append(f"{name!r}: {urteile}")

    assert not abweichungen, (
        "Die drei Stellen sind sich über die Kennungsform nicht einig:\n  "
        + "\n  ".join(abweichungen)
        + "\nDamit steht die Regel wieder mehrfach im Repo. Wer sie an einer Stelle "
          "weitet, lässt den Auftrag an der anderen stillschweigend liegen."
    )


def test_der_heutige_vertrag_wird_dabei_wirklich_eingehalten(tmp_path):
    """Einigkeit allein genügt nicht — drei Stellen können sich auch einig irren.

    Ohne diesen Wächter bestünde der erste, wenn alle drei jeden Namen annähmen. Er
    hält darum die heutige Form fest: ``vis-<zahl>-<sechs kleine Hexziffern>``.
    """
    store = tmp_path / "store"
    store.mkdir()
    for name in NAMEN:
        _lege_auftrag_an(store, name)

    gefunden = {p.name for p in bruecke.offene_auftraege(store)}
    assert gefunden == {"vis-1-abc123", "vis-1755600000-0f9e2a",
                        "vis-20260922120000-0f9e2a"}


# --------------------------------------------------------------------------------------
# 2 · Die Quelle erreicht den Weg, den das Produkt wirklich geht
# --------------------------------------------------------------------------------------

def test_eine_geaenderte_quelle_aendert_den_produktweg_der_bruecke(tmp_path, monkeypatch):
    """Die Probe auf die Naht: Wird die eine Quelle gewechselt, folgt die Brücke.

    Nachgestellt wird der Fall, der den Befund ausmacht — die fremde Warteschlange
    weitet ihre Kennungsform, und geändert wird die Stelle, an der der Vertrag geprüft
    wird. Danach muss der Ordner in der **neuen** Form gefunden werden und der in der
    alten liegen bleiben. Eine eigene Kopie in der Brücke bestünde diesen Wächter nicht,
    auch keine, die heute gleich lautet: Sie würde beim Laden des Moduls eingefroren.

    Geprüft wird über ``offene_auftraege`` — der Weg, den ein Auftrag wirklich geht.
    Genau dort lag das stille Überspringen.
    """
    monkeypatch.setattr(
        kosmo_szene, "ist_fremde_job_id",
        lambda wert: isinstance(wert, str) and wert.startswith("neu-"))

    store = tmp_path / "store"
    store.mkdir()
    _lege_auftrag_an(store, "neu-0815")
    _lege_auftrag_an(store, "vis-1755600000-0f9e2a")

    gefunden = {p.name for p in bruecke.offene_auftraege(store)}
    assert gefunden == {"neu-0815"}, (
        "Die Brücke filtert nicht über die eine Quelle, sondern über eine eigene Kopie "
        "der Regel. Damit übergeht sie jeden Auftragsordner, dessen Form dort ergänzt "
        "wurde — stillschweigend."
    )


def test_die_meldung_ueber_den_ordnernamen_haengt_an_derselben_quelle(tmp_path,
                                                                     monkeypatch):
    """Die zweite Stelle in der Brücke: die Warnung beim Lesen eines Auftrags.

    ``lies_auftrag`` meldet einen Ordnernamen, der nicht ihrer Form entspricht. Auch
    diese Meldung muss der einen Quelle folgen — sonst warnt die Brücke über eine Form,
    die drüben längst gültig ist, und der Leser lernt, die Warnung zu übergehen.
    """
    monkeypatch.setattr(
        kosmo_szene, "ist_fremde_job_id",
        lambda wert: isinstance(wert, str) and wert.startswith("neu-"))

    store = tmp_path / "store"
    store.mkdir()
    neu = _lege_auftrag_an(store, "neu-0815")
    alt = _lege_auftrag_an(store, "vis-1755600000-0f9e2a")

    def nennt_den_ordnernamen(ordner: Path) -> bool:
        gelesen = bruecke.lies_auftrag(ordner)
        return any("Ordnername" in w for w in gelesen["warnungen"])

    assert not nennt_den_ordnernamen(neu)
    assert nennt_den_ordnernamen(alt)


# --------------------------------------------------------------------------------------
# 3 · Keine zweite Kopie — die Prüfung auf Abwesenheit
# --------------------------------------------------------------------------------------

#: Die Regel als **Wert**. Sie darf in der Bibliothek genau einmal vorkommen.
#:
#: Verglichen wird der Wert der Zeichenkette, nicht ihre Schreibweise: ``r"^vis-\d+…"``
#: und ``"^vis-\\d+…"`` sind derselbe Wert. Bis zum 22.09.2026 suchte dieser Wächter
#: die rohe Schreibweise als Text — eine gewöhnlich geschriebene Kopie wäre ihm
#: entgangen, obwohl seine Fehlermeldung jede Kopie versprach (Durchsicht 22.09.2026).
REGEL = r"^vis-\d+-[0-9a-f]{6}$"


def _fundstellen_der_regel(wurzel: Path) -> list[str]:
    """Jede Zeichenkette in der Bibliothek, deren **Wert** die Regel ist.

    Docstrings und Kommentare, die die Regel nur erwähnen, zählen nicht: Ihr Wert ist
    ein ganzer Satz, nicht die Regel. Gezählt wird, was ein ``re.compile`` bekommen
    könnte.
    """
    fundstellen = []
    for datei in sorted(wurzel.rglob("*.py")):
        if "__pycache__" in datei.parts:
            continue
        baum = ast.parse(datei.read_text(encoding="utf-8"))
        for knoten in ast.walk(baum):
            if isinstance(knoten, ast.Constant) and knoten.value == REGEL:
                fundstellen.append(f"{datei.relative_to(wurzel)}:{knoten.lineno}")
    return fundstellen


def test_die_regel_steht_genau_einmal_in_der_bibliothek():
    """Eine zweite Kopie lautet am Tag ihrer Entstehung gleich — und driftet danach.

    Die beiden Wächter oben messen die Wirkung und fangen darum nur eine Kopie, die
    **schon** abweicht. Eine frisch angelegte, gleichlautende Kopie fangen sie nicht:
    Sie ist der Zustand, in dem dieses Repo bis zum 22.09.2026 war, und genau dieser
    Zustand war das Problem.

    Darum hier die einzige zulässige Textprüfung — die auf die **Abwesenheit** einer
    Zutat: Die Regel steht ausgeschrieben in ``kosmo_szene`` und sonst nirgends.
    """
    wurzel = Path(__file__).resolve().parents[1] / "src" / "aiimaging"
    fundstellen = _fundstellen_der_regel(wurzel)

    assert len(fundstellen) == 1 and fundstellen[0].startswith("kosmo_szene.py:"), (
        f"Die Kennungsform der fremden Warteschlange steht an {len(fundstellen)} "
        f"Stellen ausgeschrieben: {', '.join(fundstellen) or '(keiner)'}. Sie gehört "
        f"an genau eine — dorthin, wo der Vertrag geprüft wird (kosmo_szene). Jede "
        f"weitere Kopie lautet heute gleich und morgen nicht mehr."
    )


@pytest.mark.parametrize("modul,name", [
    (bruecke, "VERZEICHNIS_MUSTER"),
    (kosmo_naht, "FREMDES_JOB_ID_MUSTER"),
])
def test_keine_zweite_kompilierte_fassung_der_regel(modul, name):
    """Und auch kein zweites Musterobjekt hinter einem der alten Namen.

    ``bruecke`` führt die Regel gar nicht mehr; ``kosmo_naht`` behält den Namen als
    Auskunft, aber er zeigt auf **dasselbe** Objekt wie die Quelle. Ein eigenes
    ``re.compile`` hinter einem dieser Namen wäre die Kopie von neuem — nur eine, die
    man beim Lesen für eine Weiterleitung hält.
    """
    muster = getattr(modul, name, None)
    assert muster is None or muster is kosmo_szene.FREMDE_JOB_ID


def test_auch_eine_gewoehnlich_geschriebene_kopie_wird_gefunden(tmp_path):
    """Die Gegenprobe zum Wächter oben: Er muss beide Schreibweisen fangen.

    Nachgestellt wird die Kopie, die die Durchsicht vom 22.09.2026 fand — mit
    verdoppelten Rückstrichen statt roh geschrieben. Ein Docstring, der die Regel nur
    erwähnt, darf dagegen nicht zählen.
    """
    (tmp_path / "roh.py").write_text(
        'import re\nA = re.compile(r"^vis-\\d+-[0-9a-f]{6}$")\n', encoding="utf-8")
    (tmp_path / "gewoehnlich.py").write_text(
        'import re\nB = re.compile("^vis-\\\\d+-[0-9a-f]{6}$")\n', encoding="utf-8")
    (tmp_path / "erwaehnt.py").write_text(
        '"""Die Form ist ^vis-\\d+-[0-9a-f]{6}$, siehe kosmo_szene."""\n',
        encoding="utf-8")

    gefunden = sorted(f.split(":")[0] for f in _fundstellen_der_regel(tmp_path))
    assert gefunden == ["gewoehnlich.py", "roh.py"]
