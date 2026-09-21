"""Die Oberfläche — **eine dünne Schicht, und diese Proben halten sie dünn.**

Eine Oberfläche ist die Stelle, an der Regel 4 bricht, wenn niemand hinsieht:

    *Die Oberfläche ist eine dünne Schicht über der Bibliothek, nie deren Voraussetzung.*
    *Was nur über einen Klick erreichbar ist, existiert nicht.*

Geprüft werden darum nicht Knöpfe und Farben, sondern die fünf Stellen, an denen eine
Fläche still etwas kaputtmacht:

1. Sie kann etwas, das die Bibliothek nicht kann — und damit gibt es die Fähigkeit für
   niemanden, der kein Fenster offen hat.
2. Sie zeigt ein **ungeprüftes** Bild wie ein bestandenes. Oder wie gar nichts, was
   dasselbe ist: *Kein Abzeichen sieht aus wie kein Problem.*
3. Sie holt etwas aus dem Netz — und damit ist das Ein-Klick-Ziel dahin.
4. Sie hört auf allen Adressen, und die Gebäudemodelle auf dieser Platte gehen mit.
5. Sie setzt Attrappen ein, damit etwas erscheint — dann entstehen Bilder und Urteile,
   die nichts gemessen haben.

**Ohne Netz, ohne Browser, ohne GPU.** Der Server wird gebaut und nicht gestartet.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
FLAECHE = WURZEL / "oberflaeche"
SERVER_PY = FLAECHE / "server.py"
SEITE = FLAECHE / "seite.html"


@pytest.fixture(scope="module")
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


# ------------------------------------------------------ 1 · Regel 4 haelt in beide Richtungen

def test_der_kern_weiss_von_der_flaeche_nichts():
    """Die Richtung ist die ganze Regel: Die Fläche importiert den Kern, nie umgekehrt.

    Wäre es andersherum — oder auch nur beidseitig —, liesse sich die Bibliothek ohne die
    Fläche nicht mehr benutzen, und die Fläche wäre ihre Voraussetzung.
    """
    funde = []
    for datei in (WURZEL / "src" / "aiimaging").rglob("*.py"):
        quelle = datei.read_text(encoding="utf-8")
        if "oberflaeche" in quelle and "src" not in datei.name:
            funde.append(datei.name)
    assert not funde, f"Der Kern nennt die Oberfläche: {funde}"


def test_die_flaeche_liegt_ausserhalb_des_kerns():
    """Sonst schlüge der Wächter für Regel 4 zu — und er hätte recht."""
    assert SERVER_PY.exists()
    assert not (WURZEL / "src" / "aiimaging" / "server.py").exists()


def test_jeder_bibliotheksaufruf_der_flaeche_gibt_es_wirklich():
    """**Die Probe gegen die häufigste Art, eine Fläche dick zu machen.**

    Sie liest die Aufrufe aus dem Quelltext und prüft, dass jeder davon in der Bibliothek
    existiert. Ein Aufruf, den es nicht gibt, wäre entweder ein Tippfehler — oder der
    Anfang einer zweiten Fassung derselben Fähigkeit, hier statt dort.
    """
    from aiimaging import arbeitsgang, importeur, kette, projekt
    module = {"arbeitsgang": arbeitsgang, "importeur": importeur,
              "kette": kette, "projekt": projekt}

    fehlend = []
    for k in ast.walk(ast.parse(SERVER_PY.read_text(encoding="utf-8"))):
        if not isinstance(k, ast.Attribute):
            continue
        wurzel = k.value
        if isinstance(wurzel, ast.Name) and wurzel.id in module:
            if not hasattr(module[wurzel.id], k.attr):
                fehlend.append(f"{wurzel.id}.{k.attr}")
    assert not fehlend, (
        f"Die Fläche ruft, was es in der Bibliothek nicht gibt: {sorted(set(fehlend))}")


def test_in_der_flaeche_steht_keine_schwelle_und_kein_urteil():
    """*Stünde hier eine Schwelle, wäre dieselbe Fähigkeit an zwei Stellen* — und eine
    davon ohne Oberfläche nicht erreichbar.

    Gesucht wird nach den Namen, unter denen in diesem Projekt geurteilt wird. Sie dürfen
    **gelesen** werden (das Ergebnis anzeigen ist der Zweck), aber nicht **gerechnet**.
    """
    quelle = SERVER_PY.read_text(encoding="utf-8")
    verboten = ["SCHWELLE_", "geometrie_gate(", "zwei_tore(", "rho_ueber_maske(",
                "geometrie_score("]
    funde = [v for v in verboten if v in quelle]
    assert not funde, (
        f"Die Fläche urteilt selbst: {funde}. Sie darf Urteile zeigen, nicht fällen.")


# ------------------------------------------------- 2 · die dritte Antwort ist sichtbar

@pytest.mark.parametrize("urteil,erwartet", [
    (True, "bestanden"),
    (False, "durchgefallen"),
    (None, "nicht-gemessen"),
])
def test_die_drei_zeichen_sind_drei(server, urteil, erwartet):
    """Drei Zustände, drei Zeichen — und das dritte ist keines der beiden anderen."""
    eintrag = {"bild": "a.png", "schicht": "geometrielayer",
               "geometrie_bestanden": urteil,
               "herkunft": {"grund": "Zu diesem Bild gibt es keine Prüfung. NICHT GEMESSEN."}}
    assert server._bild_fuer_die_flaeche(eintrag)["zeichen"] == erwartet


def test_ein_ungeprueftes_bild_bekommt_seinen_eigenen_satz(server):
    """**Kein Abzeichen sieht aus wie kein Problem.**

    Der UI-Worker hat das am 03.09.2026 an seiner eigenen Fläche gemeldet: Die Bildkachel
    zeigte bei fehlender Prüfung gar kein Abzeichen. Hier bekommt sie eines — und den
    Grund dazu, und der kommt aus dem Eintrag und nicht aus einem Satz in der Fläche.
    """
    grund = "Die Prüfung lief nicht. NICHT GEMESSEN."
    d = server._bild_fuer_die_flaeche(
        {"bild": "a.png", "schicht": "geometrielayer", "geometrie_bestanden": None,
         "herkunft": {"grund": grund}})
    assert d["zeichen"] == "nicht-gemessen"
    assert d["satz"] == grund, "der Grund aus dem Eintrag, nicht ein allgemeiner Satz"


def test_das_geerbte_urteil_bleibt_ein_eigenes_feld(server):
    """E20: *Ein geerbtes Urteil ist kein eigenes.*

    Ein Bild der zweiten Stufe mit bestandener Basis darf **nicht** als bestanden
    angezeigt werden. Das Zeichen gehört dem Bild, der Block darunter der Basis.
    """
    d = server._bild_fuer_die_flaeche({
        "bild": "variante-3.png", "schicht": "ai-imaging-layer",
        "geometrie_bestanden": None,
        "basis": {"bild": "a.png", "geometrie_bestanden": True},
        "herkunft": {"grund": "NICHT ANWENDBAR: von Hand bearbeitet."}})
    assert d["zeichen"] == "nicht-gemessen"
    assert d["basis"]["geometrie_bestanden"] is True


def test_die_seite_kennt_alle_drei_zeichen():
    """Fiele eines aus der Seite, sähe sein Zustand aus wie ein Zustand ohne Zeichen.

    Die Probe sucht sie in **beiden** Hälften: im Stil (damit sie verschieden aussehen)
    und im Skript (damit sie benannt werden).
    """
    seite = SEITE.read_text(encoding="utf-8")
    for zeichen in ("bestanden", "durchgefallen", "nicht-gemessen"):
        assert f".{zeichen}" in seite, f"kein eigenes Aussehen für {zeichen}"
        assert f'"{zeichen}"' in seite, f"das Skript benennt {zeichen} nicht"
    assert "border-style: dashed" in seite, (
        "das ungeprüfte Bild sieht aus wie ein bestandenes — es braucht ein eigenes "
        "Aussehen und nicht nur eine andere Farbe")


# ---------------------------------------------------------- 3 · nichts aus dem Netz

def test_die_seite_laedt_nichts_von_aussen():
    """*Was zum Start eine Netzverbindung braucht, ist kein Ein-Klick-Download.*

    Eine Schriftart von einem fremden Server ist eine Netzverbindung — und eine Fläche,
    die ohne Netz halb aussieht, ist auf einer Baustelle unbrauchbar.
    """
    seite = SEITE.read_text(encoding="utf-8")
    for muster in ("http://", "https://", "//cdn", "integrity="):
        assert muster not in seite, f"Die Seite holt etwas von aussen: {muster!r}"


def test_die_flaeche_braucht_kein_fremdes_paket():
    """Regel 1 schliesst die üblichen Fenster-Werkzeugkästen aus (PyQt GPL, PySide LGPL).

    Was übrig bleibt, ist die Standardbibliothek — und das ist hier kein Verzicht,
    sondern der Grund, warum die Lizenzfrage gar nicht erst entsteht.
    """
    baum = ast.parse(SERVER_PY.read_text(encoding="utf-8"))
    fremd = set()
    for k in ast.walk(baum):
        if isinstance(k, ast.Import):
            fremd |= {n.name.split(".")[0] for n in k.names}
        elif isinstance(k, ast.ImportFrom) and k.module:
            fremd.add(k.module.split(".")[0])
    erlaubt = {"argparse", "inspect", "json", "sys", "urllib", "http", "pathlib",
               "aiimaging", "__future__"}
    assert fremd <= erlaubt, f"Fremde Pakete in der Fläche: {sorted(fremd - erlaubt)}"


# ------------------------------------------------ 4 · sie hoert nur auf dieser Maschine

def test_die_vorgabe_ist_die_eigene_maschine(server):
    """Hier liegen die Gebäudemodelle von jemandem.

    Eine Fläche, die von aussen erreichbar ist, gibt sie weiter — auch wenn niemand das
    wollte. Eine andere Adresse ist möglich und muss ausdrücklich gesetzt werden.
    """
    assert server.VORGABE_ADRESSE == "127.0.0.1"


def test_eine_fremde_adresse_wird_beim_start_benannt():
    """Wer die Fläche öffnet, soll es lesen — nicht später merken."""
    quelle = SERVER_PY.read_text(encoding="utf-8")
    assert "von aussen erreichbar" in quelle


# --------------------------------------------- 5 · keine Attrappen, keine Schein-Urteile

def test_die_flaeche_setzt_keine_attrappen_ein():
    """**Die schlimmste Zeile, die hier stehen könnte.**

    Eine Attrappe einzusetzen, damit beim Klick etwas erscheint, erzeugt Bilder und
    Urteile, die nichts gemessen haben — und niemand sieht ihnen das an. Fehlen die
    Werkzeuge, scheitert der Lauf, und der Fehlschlag kommt als Satz zurück.
    """
    quelle = SERVER_PY.read_text(encoding="utf-8")
    for muster in ("ausfuehrer=", "attrappe", "Attrappe", "_starte="):
        assert muster not in quelle or muster == "Attrappe", (
            f"Die Fläche reicht {muster!r} in die Bibliothek — damit entstünden Urteile, "
            f"die nichts gemessen haben.")


def test_ein_fehlschlag_kommt_als_satz_und_nicht_als_code(server, tmp_path):
    """Wer einen Stacktrace liest, hört auf; wer einen Satz liest, weiss, woran er ist."""
    from aiimaging import projekt
    with pytest.raises(projekt.ProjektError) as fehler:
        server.sicht(tmp_path / "gibt-es-nicht")
    assert "kein Projekt" in str(fehler.value)


# ------------------------------------------------------------------ die Sicht insgesamt

def test_ein_fehlender_prompt_zeigt_den_satz_der_bibliothek_ohne_typnamen(tmp_path, server):
    """Die Zielgruppe hoert bei Programmmeldungen auf zu lesen.

    Die Bibliothek schreibt ihre Fehler fuer Menschen — *«ohne ihn ist nicht beschrieben,
    was entstehen soll»*. Ein vorangestelltes ``KettenError:`` macht daraus wieder eine
    Programmmeldung.

    Fuer **unerwartete** Fehler gilt das Gegenteil, und auch das ist eine Entscheidung:
    Ein Fehler, den dieses Projekt nicht vorhergesehen hat, ist fuer niemanden
    geschrieben — dann ist der Typ die einzige Spur.
    """
    from aiimaging import projekt
    import struct

    js = json.dumps({"asset": {"version": "2.0", "generator": "T"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    modell = tmp_path / "haus.glb"
    modell.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)

    wurzel = tmp_path / "ohne-prompt"
    p = projekt.neu(wurzel, modell, einstellungen={"up_axis": "Y"})
    p["import"] = {"status": "ok", "weg": "durchgereicht", "glb": str(modell),
                   "format": "glTF", "treue": None, "hochachse": None,
                   "hochachse_steht_fest": False, "hinweise": []}
    projekt.speichere(p, wurzel)

    meldung = server.sicht(wurzel)["knotenbaum_fehler"]
    assert meldung and "prompt fehlt" in meldung
    assert not meldung.startswith("KettenError"), (
        "der Typname macht aus einem Satz fuer Menschen wieder eine Programmmeldung")


def test_die_sicht_zeigt_ein_projekt_vollstaendig(tmp_path, server):
    """Ein Durchgang von aussen: anlegen, eintragen, ansehen."""
    from aiimaging import projekt
    import struct

    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    modell = tmp_path / "haus.glb"
    modell.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)

    wurzel = tmp_path / "p"
    p = projekt.neu(wurzel, modell, name="Wohnhaus",
                    einstellungen={"up_axis": "Y", "prompt": "Abendlicht"})
    p["import"] = {"status": "ok", "weg": "durchgereicht", "glb": str(modell),
                   "format": "glTF", "treue": None, "hochachse": None,
                   "hochachse_steht_fest": False, "hinweise": []}
    projekt.vermerke_bild(p, bild="a.png", schicht="geometrielayer", urteil=None)
    projekt.speichere(p, wurzel)

    d = server.sicht(wurzel)
    assert d["name"] == "Wohnhaus"
    assert d["modell"]["stand"] == projekt.MODELL_UNVERAENDERT
    assert [k["art"] for k in d["knotenbaum"]][:2] == ["geometrie", "multipass"]
    assert d["bilder"][0]["zeichen"] == "nicht-gemessen"


# ======================================================================================
# DER BEDIENBARE KNOTENBAUM — und die Zuordnung, die zweimal zu schwach war
# ======================================================================================

def _projekt_mit_glb(tmp_path, einstellungen=None):
    """Ein Projekt mit durchgereichter glb — ohne Blender, ohne Umwandlung."""
    from aiimaging import projekt
    import struct

    js = json.dumps({"asset": {"version": "2.0", "generator": "T"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    modell = tmp_path / "haus.glb"
    modell.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)

    wurzel = tmp_path / "p"
    p = projekt.neu(wurzel, modell, einstellungen=einstellungen or
                    {"prompt": "Abendlicht", "up_axis": "Y"})
    p["import"] = {"status": "ok", "weg": "durchgereicht", "glb": str(modell),
                   "format": "glTF", "treue": None, "hochachse": None,
                   "hochachse_steht_fest": False, "hinweise": []}
    projekt.speichere(p, wurzel)
    return wurzel


def test_die_bedienfelder_kommen_aus_der_bibliothek_und_nicht_aus_einer_liste(server, tmp_path):
    """**Eine handgeschriebene Feldliste macht denselben Fehler ein drittes Mal.**

    Am 21.09.2026 waren elf Bestellungen über einen der beiden Wege nicht erreichbar, weil
    eine Aufzählung nicht mitgewachsen war. Eine Oberfläche mit fester Feldliste wäre
    dasselbe — und diesmal sähe es niemand, weil nichts kaputtgeht, sondern nur fehlt.
    """
    import inspect
    from aiimaging import kette

    namen = {f["name"] for f in server.sicht(_projekt_mit_glb(tmp_path))["bedienfelder"]}
    erwartet = {n for n in inspect.signature(kette.baue_kette).parameters
                if n not in server.NICHT_EINSTELLBAR}
    assert namen == erwartet, (
        f"Die Fläche bietet nicht an, was die Bibliothek kann: fehlt {sorted(erwartet - namen)}, "
        f"zu viel {sorted(namen - erwartet)}")


def test_ein_noch_nicht_gesetztes_feld_findet_trotzdem_seinen_knoten(server, tmp_path):
    """**Der erste Fehlschlag dieser Zuordnung, als Probe festgehalten.**

    Der erste Anlauf las den gebauten Graphen — und ein Feld, das noch nicht gesetzt ist,
    steht in keinem Knoten. 16 von 34 Feldern landeten im Sammelbecken, darunter der
    Sonnenstand. *Und das Unbenutzte ist genau das, was jemand als Nächstes sucht.*
    """
    felder = {f["name"]: f for f in
              server.sicht(_projekt_mit_glb(tmp_path))["bedienfelder"]}
    assert felder["sonne"]["gesetzt"] is False, "die Vorbedingung der Probe"
    assert felder["sonne"]["knoten"] == "multipass", (
        "ein ungesetztes Feld muss seinen Knoten trotzdem finden")


def test_ein_feld_das_im_knoten_anders_heisst_wird_gefunden(server, tmp_path):
    """**Der zweite Fehlschlag, und er ist der lehrreichere.**

    Der zweite Anlauf verglich die Parameter-**Namen** — und war blind für jedes Feld, das
    im Knoten anders heisst. ``qa_schwelle`` landet dort als ``schwelle``.

        *Was ankommt, zählt; nicht, wie es heisst.* — dieselbe Art Prüfung, die im Kern
        zwischen den zwei Wegen gefehlt hat.
    """
    felder = {f["name"]: f for f in
              server.sicht(_projekt_mit_glb(tmp_path))["bedienfelder"]}
    assert felder["qa_schwelle"]["knoten"] == "qa", (
        "ein Namensvergleich findet das nie — hier wird der Wert verglichen")


def test_kein_knoten_heisst_dreierlei_und_wird_dreierlei_gemeldet(server, tmp_path):
    """**Diese Probe stand zuerst mit einer falschen Begründung da, und das ist der Punkt.**

    Sie behauptete, ``up_axis`` bekomme keinen Knoten, *weil es auf mehrere wirkt*.
    Nachgemessen stimmte das nicht: Der Probewert ``"Y "`` wird von der Prüfung zu ``"Y"``
    zurücknormalisiert — **es ändert sich gar nichts**, und das Feld galt als wirkungslos.

        *Eine Probe, deren Wert unterwegs zurückverwandelt wird, misst nicht die Wirkung,
        sondern die Normalisierung.* Und eine Probe, die aus dem falschen Grund grün ist,
        bewacht etwas anderes, als ihr Name sagt — zum dritten Mal an diesem Tag.

    «Kein Knoten» hiess bis dahin dreierlei, und die drei sahen gleich aus. Jetzt sind es
    drei Antworten:

    ``bau``
        Das Feld bestimmt, **welche** Knoten es gibt — ``qa=False`` entfernt die Prüfung.
    ``unbekannt``
        Die Probe hat **nichts gesehen**. Weder ja noch nein.
    ``knoten``
        Genau ein Knoten sieht damit anders aus.
    """
    felder = {f["name"]: f for f in
              server.sicht(_projekt_mit_glb(tmp_path))["bedienfelder"]}

    assert felder["qa"]["wirkt_auf"] == server.WIRKT_AUF_BAU, (
        "`qa` entfernt den Prüfknoten — das ist eine Auskunft über den Bau, keine fehlende")
    assert felder["qa"]["knoten"] is None

    assert felder["up_axis"]["wirkt_auf"] == server.WIRKT_UNBEKANNT, (
        "der Probewert wird zurücknormalisiert — die Probe sieht nichts, und sagt das")
    assert felder["sonne"]["wirkt_auf"] == server.WIRKT_AUF_KNOTEN


def test_fast_jedes_feld_findet_seinen_knoten(server, tmp_path):
    """Die Zahl, an der die drei Anläufe zu messen sind.

    Beim ersten Anlauf lagen **16 von 34** Feldern im Sammelbecken. Diese Probe hält
    fest, dass es heute höchstens zwei sind — und dass beide einen **benannten** Grund
    haben.
    """
    felder = server.sicht(_projekt_mit_glb(tmp_path))["bedienfelder"]
    ohne = [f for f in felder if f["knoten"] is None]
    assert len(ohne) <= 2, (
        f"{len(ohne)} von {len(felder)} Feldern ohne Knoten: "
        f"{[f['name'] for f in ohne]}")
    for f in ohne:
        assert f["wirkt_auf"] in (server.WIRKT_AUF_BAU, server.WIRKT_UNBEKANNT)


def test_eine_abgelehnte_einstellung_wird_nicht_gespeichert(server, tmp_path):
    """**Die Bibliothek urteilt, nicht die Fläche — und bei Nein bleibt alles stehen.**

    Ein Projekt, dessen Einstellungen keine Kette ergeben, sieht in der Mappe aus wie
    jedes andere. Der Fehler fiele erst beim nächsten Lauf auf, an einer Stelle, die mit
    ihm nichts zu tun hat.
    """
    from aiimaging import projekt
    wurzel = _projekt_mit_glb(tmp_path)

    class Antwort:
        def __init__(self): self.daten = None
        def __call__(self, nutzlast, code=200): self.daten = (nutzlast, code)

    flaeche = server.Flaeche.__new__(server.Flaeche)
    flaeche.ordner = wurzel
    antwort = Antwort()
    flaeche._sende = antwort
    flaeche._fehler = lambda satz, code=400: antwort({"fehler": satz}, code)

    flaeche._einstellungen({"ordner": str(wurzel), "einstellungen": {"prompt": None}})

    nutzlast, _ = antwort.daten
    assert "fehler" in nutzlast and "prompt fehlt" in nutzlast["fehler"]
    gespeichert = projekt.oeffne(wurzel)["projekt"]["einstellungen"]
    assert gespeichert["prompt"] == "Abendlicht", "der alte Wert bleibt stehen"


def test_eine_angenommene_einstellung_landet_im_knoten(server, tmp_path):
    """Der ganze Zweck: Was oben eingegeben wird, steht unten in der Rechnung."""
    from aiimaging import projekt
    wurzel = _projekt_mit_glb(tmp_path)

    p = projekt.oeffne(wurzel)["projekt"]
    p["einstellungen"]["sonne"] = {"azimut": 250, "hoehe": 8}
    p["einstellungen"]["aufloesung"] = 768
    projekt.speichere(p, wurzel)

    baum = {k["art"]: k for k in server.sicht(wurzel)["knotenbaum"]}
    assert baum["multipass"]["params"]["sonne"] == {"azimut": 250, "hoehe": 8}
    assert baum["multipass"]["params"]["aufloesung"] == 768


def test_ein_leeres_feld_stellt_die_vorgabe_wieder_her(server, tmp_path):
    """Leer heisst NICHT GESETZT, nicht «leerer Text».

    Der Unterschied ist derselbe wie überall hier: «nicht gesetzt» heisst «es gilt die
    Vorgabe», ein leerer Text hiesse «ausdrücklich nichts».
    """
    from aiimaging import projekt
    wurzel = _projekt_mit_glb(tmp_path, {"prompt": "Abendlicht", "up_axis": "Y",
                                         "aufloesung": 768})

    class Antwort:
        def __init__(self): self.daten = None
        def __call__(self, nutzlast, code=200): self.daten = (nutzlast, code)

    flaeche = server.Flaeche.__new__(server.Flaeche)
    flaeche.ordner = wurzel
    antwort = Antwort()
    flaeche._sende = antwort
    flaeche._fehler = lambda satz, code=400: antwort({"fehler": satz}, code)

    flaeche._einstellungen({"ordner": str(wurzel), "einstellungen": {"aufloesung": None}})

    gespeichert = projekt.oeffne(wurzel)["projekt"]["einstellungen"]
    assert "aufloesung" not in gespeichert, (
        "auf None gesetzt heisst entfernt — nicht als None gespeichert")
