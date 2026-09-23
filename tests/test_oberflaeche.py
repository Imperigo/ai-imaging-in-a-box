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
import io
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
    # GEGEN DIE STANDARDBIBLIOTHEK SELBST, nicht gegen eine Liste von Hand.
    #
    # Bis zum 21.09.2026 stand hier eine aufgezaehlte Erlaubnisliste. Sie hat beim ersten
    # `import base64` angeschlagen — einem Modul der Standardbibliothek, an dem unter
    # Regel 1 nichts auszusetzen ist. *Ein Waechter, der bei jedem Ausbau von Hand
    # nachgezogen werden muss, wird irgendwann weit gestellt statt nachgezogen.*
    #
    # `sys.stdlib_module_names` kennt sie alle. Der Waechter wird dadurch SCHAERFER: Er
    # erlaubt jedes Standardmodul und weiterhin kein einziges fremdes Paket.
    erlaubt = set(sys.stdlib_module_names) | {"aiimaging", "__future__"}
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
                if n not in server.NICHT_EINSTELLBAR and n not in kette.MESSSCHALTER}
    assert namen == erwartet, (
        f"Die Fläche bietet nicht an, was die Bibliothek kann: fehlt {sorted(erwartet - namen)}, "
        f"zu viel {sorted(namen - erwartet)}")


def test_ein_messschalter_erscheint_nur_wenn_die_mappe_ihn_traegt(server, tmp_path):
    """**Messschalter sind kein Alltagsfeld — aber ein gesetzter bleibt sichtbar**
    (23.09.2026). Sonst rechnete eine Mappe anders, als ihre Anzeige sagt."""
    from aiimaging import kette

    assert set(kette.MESSSCHALTER) == {"ferne_abstand", "tiefe_invertieren"}
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    ohne = {f["name"] for f in server.sicht(_projekt_mit_glb(tmp_path / "a"))["bedienfelder"]}
    assert not ohne & set(kette.MESSSCHALTER)
    mit = {f["name"]: f for f in server.sicht(_projekt_mit_glb(
        tmp_path / "b", {"prompt": "Abendlicht", "up_axis": "Y",
                         "ferne_abstand": 0.15}))["bedienfelder"]}
    assert mit["ferne_abstand"]["gesetzt"] is True and mit["ferne_abstand"]["wert"] == 0.15
    assert "tiefe_invertieren" not in mit


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


# --------------------------------------------- 6 · Die Flaeche liefert Dateien aus
#
# Seit dem 21.09.2026 zeigt sie Bilder statt Dateinamen. Damit entscheidet sie darueber,
# was von der Platte dieses Rechners in einen Browser geht — und das ist eine andere
# Sorte Verantwortung als eine Liste anzuzeigen.
#
# Sie hoert nur auf 127.0.0.1. Trotzdem steht die Sperre hier:
#
#     Eine zweite Sperre, die nur dann noetig wird, wenn die erste faellt, ist genau die
#     Sperre, die man baut, solange nichts passiert ist.

def test_ein_absoluter_pfad_kommt_nicht_durch(server, tmp_path):
    """Der Fall, den `Path.joinpath` still erfuellt.

    ``ordner / "/etc/passwd"`` ergibt ``/etc/passwd`` — der ganze bisherige Pfad wird
    ersetzt, und nichts daran sieht nach einem Fehler aus.

    **Geprueft wird auch der SATZ, und das hat einen gemessenen Grund.** Eine
    Mutationsprobe am 21.09.2026 hat die Namenssperre ausgeschaltet: Alle Proben blieben
    gruen, weil die Aufloesung des Pfades denselben Fall ohnehin faengt. Die Namenssperre
    traegt also nichts zur Sicherheit bei — sie traegt die **bessere Auskunft**, und nur
    dafuer steht sie noch da. Wer `/etc/passwd` eingibt, soll nicht ueber Verweise
    belehrt werden, die hier keine Rolle spielen.

        *Ein Waechter, der nichts faengt, was der naechste nicht auch faengt, ist kein
        zweiter Waechter.*
    """
    with pytest.raises(server.FlaechenError) as fehler:
        server.bildpfad(tmp_path, "/etc/passwd")
    assert "heraus" in str(fehler.value), (
        "Der absolute Pfad soll den Satz ueber den Ordner bekommen, nicht den ueber "
        "Verweise — sonst ist die Namenssperre ganz ohne Wirkung und gehoert weg.")


def test_ein_aufstieg_kommt_nicht_durch(server, tmp_path):
    """`..` in irgendeinem Teil fuehrt aus dem Projektordner heraus."""
    (tmp_path / "projekt").mkdir()
    for name in ("../geheim.png", "unter/../../geheim.png"):
        with pytest.raises(server.FlaechenError):
            server.bildpfad(tmp_path / "projekt", name)


def test_ein_verweis_aus_dem_ordner_heraus_kommt_nicht_durch(server, tmp_path):
    """**Die Probe, die den Namen nicht glaubt.**

    Die ersten beiden Sperren lesen den *Namen*. Ein Verweis im Ordner heisst harmlos und
    zeigt trotzdem anderswohin. Erst der aufgeloeste Pfad beantwortet die Frage.

        *Ein Name sagt, wie etwas heisst, nicht wo es liegt.*
    """
    aussen = tmp_path / "aussen"
    aussen.mkdir()
    (aussen / "fremd.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    innen = tmp_path / "projekt"
    innen.mkdir()
    try:
        (innen / "harmlos.png").symlink_to(aussen / "fremd.png")
    except (OSError, NotImplementedError):
        pytest.skip("Dieses Dateisystem kennt keine Verweise.")

    with pytest.raises(server.FlaechenError):
        server.bildpfad(innen, "harmlos.png")


def test_die_projektdatei_selbst_wird_nicht_als_bild_ausgeliefert(server, tmp_path):
    """Sie liegt im selben Ordner und ist kein Bild. Eine Positivliste der Endungen sagt,
    was hinausgeht; eine Sperrliste kennte nur, woran schon jemand gedacht hat."""
    (tmp_path / "projekt.json").write_text("{}", encoding="utf-8")
    with pytest.raises(server.FlaechenError):
        server.bildpfad(tmp_path, "projekt.json")


def test_ein_bild_im_projektordner_kommt_durch(server, tmp_path):
    """Die Gegenprobe. **Ohne sie waeren die vier Sperren oben auch dann gruen, wenn die
    Funktion einfach immer ablehnte** — und eine Flaeche, die nie ein Bild zeigt, haette
    alle Proben bestanden."""
    (tmp_path / "ansicht-1.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    assert server.bildpfad(tmp_path, "ansicht-1.png") == (tmp_path / "ansicht-1.png")


def test_auch_ein_unterordner_im_projekt_ist_erlaubt(server, tmp_path):
    """Die Mappe darf Ordnung halten. Verboten ist der Weg HINAUS, nicht der nach unten."""
    (tmp_path / "laeufe").mkdir()
    (tmp_path / "laeufe" / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    assert server.bildpfad(tmp_path, "laeufe/a.png").is_file()


def test_eine_fehlende_datei_ist_eine_absage_mit_satz(server, tmp_path):
    """Und der Satz sagt, was los ist: Der Name steht in der Mappe, die Datei nicht.

    Nicht «404». Wer einen Zustandscode liest, hoert auf; wer einen Satz liest, weiss,
    woran er ist.
    """
    with pytest.raises(server.FlaechenError) as fehler:
        server.bildpfad(tmp_path, "weg.png")
    assert "Mappe" in str(fehler.value)


# ------------------------------------- 7 · Was die Flaeche ueber ein fehlendes Bild sagt

def _eintrag(**zusatz):
    grund = {"bild": "a.png", "schicht": "geometrielayer", "geometrie_bestanden": True}
    grund.update(zusatz)
    return grund


def test_ein_fehlendes_bild_wird_als_fehlend_gemeldet(server, tmp_path):
    """**Der Zustand, den es vor der Bildanzeige gar nicht gab.**

    Die Mappe nennt ein Bild, und die Datei ist weg — verschoben, geloescht, ein Ordner
    umbenannt. In einer Liste aus Namen sah das aus wie jedes andere Bild.

        *Ein Name ohne Datei sieht in einer Liste genauso aus wie einer mit.*
    """
    assert server._bild_fuer_die_flaeche(_eintrag(), tmp_path)["vorhanden"] is False


def test_ein_vorhandenes_bild_wird_als_vorhanden_gemeldet(server, tmp_path):
    """Die Gegenprobe — sonst genuegte ein `vorhanden: False` fuer alles."""
    (tmp_path / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    assert server._bild_fuer_die_flaeche(_eintrag(), tmp_path)["vorhanden"] is True


def test_ohne_ordner_heisst_es_unbekannt_und_nicht_weg(server):
    """Die dritte Antwort, und sie gilt auch fuer diese kleine Frage: Wo niemand
    nachgesehen hat, steht **nicht** «weg», sondern `None`."""
    assert server._bild_fuer_die_flaeche(_eintrag())["vorhanden"] is None


# ------------------------------------------- 8 · Das Abzeichen sitzt AUF dem Bild

def test_die_seite_setzt_das_abzeichen_in_den_bildrahmen():
    """**Die Auflage, um die es bei dieser Flaeche ueberhaupt geht.**

    Ein Abzeichen neben dem Bild faellt beim ersten Weiterreichen ab — ein
    Bildschirmfoto, ein Ausschnitt, und uebrig bleibt das Bild ohne seinen Vorbehalt.

        *Ein Vorbehalt, der beim ersten Weiterreichen abfaellt, ist kein Vorbehalt.*

    Geprueft wird, was maschinell entscheidbar ist: dass die Auflage im Rahmen entsteht,
    in dem auch das Bild liegt — und zwar in **jedem** Zweig, auch dort, wo die Datei
    fehlt.
    """
    text = SEITE.read_text(encoding="utf-8")
    baustein = text.split("function bildrahmen", 1)[1].split("\nfunction ", 1)[0]

    assert 'feld("div", "auflage"' in baustein, "die Auflage entsteht nicht im Rahmen"
    assert baustein.count("return rahmen") == 1, (
        "mehr als ein Ausgang aus dem Rahmenbaustein — dann kann einer davon ohne die "
        "Auflage herausfuehren, und genau der zeigt ein Bild ohne seinen Vorbehalt")


def test_die_drei_zeichen_haben_drei_verschiedene_rahmen():
    """Gleich aussehende Rahmen waeren dasselbe wie kein Abzeichen. Der ungemessene ist
    zusaetzlich **gestrichelt** — Farbe allein unterscheidet nicht, wer sie nicht sieht."""
    text = SEITE.read_text(encoding="utf-8")
    for zeichen in ("bestanden", "durchgefallen", "nicht-gemessen"):
        assert f".rahmen.{zeichen}" in text, zeichen
    strich = text.split(".rahmen.nicht-gemessen", 1)[1].split("}", 1)[0]
    assert "dashed" in strich


def test_das_bild_wird_nicht_zwischengespeichert():
    """Ein neuer Lauf schreibt unter denselben Namen. Ein Browser, der das alte Bild
    behaelt, zeigt ein Ergebnis, das es nicht mehr gibt — **neben einem Urteil, das zum
    neuen gehoert.** Das ist schlimmer als langsam."""
    assert 'self.send_header("Cache-Control", "no-store")' in \
        SERVER_PY.read_text(encoding="utf-8")


def test_der_bildname_wird_kodiert_und_nicht_eingeklebt():
    """Ein Dateiname darf ein `&` enthalten. Ohne Kodierung waere ab dort ein zweiter
    Parameter daraus geworden, und das Bild waere ein anderes."""
    baustein = SEITE.read_text(encoding="utf-8").split("function bildweg", 1)[1] \
                                                .split("\n}", 1)[0]
    assert baustein.count("encodeURIComponent") == 2


# ------------------------------------ 9 · Die Zeichenflaeche — der Entwurfsmodus (E23)
#
# Sie ist fuer einen STIFT gebaut, nicht fuer eine Maus, die auch geht. Der Owner will
# einen «schlauen Stift»-Ablauf auf dem iPad: zeichnen, AI-imagen, Variante ansehen.
# Ob ein Browser das wirklich traegt, kann hier niemand messen — es gibt kein iPad und
# keinen Stift. Was hier geprueft wird, ist darum nicht das Gefuehl, sondern dass die
# Seite die einzigen Ereignisse benutzt, die Druck und Stiftart ueberhaupt liefern.

def test_die_seite_benutzt_zeigerereignisse_und_nicht_maus_und_beruehrung_getrennt():
    """`PointerEvent` ist der einzige Weg, der `pressure` und `pointerType` liefert —
    und der fuer Maus, Finger und Stift derselbe ist.

    Maus- und Beruehrungsereignisse daneben waeren derselbe Code dreimal, und der dritte
    veraltet zuerst.
    """
    text = SEITE.read_text(encoding="utf-8")

    assert "pointerdown" in text and "pointermove" in text
    for alt in ("mousedown", "touchstart", "mousemove", "touchmove"):
        assert alt not in text, f"{alt} steht daneben — dann gibt es zwei Wege"


def test_die_zeichenflaeche_laesst_das_geraet_nicht_die_seite_schieben():
    """`touch-action: none` ist keine Kosmetik. Ohne das schiebt ein Tablet beim Zeichnen
    die Seite, statt einen Strich zu machen — und die Flaeche waere mit dem Finger oder
    dem Stift schlicht nicht bedienbar."""
    text = SEITE.read_text(encoding="utf-8")
    regel = text.split(".zeichenflaeche canvas", 1)[1].split("}", 1)[0]

    assert "touch-action: none" in regel


def test_der_druck_wirkt_nur_beim_stift():
    """Eine Maus meldet `pressure` 0. Wer daraus eine Breite rechnet, zieht mit der Maus
    Haarlinien — und es saehe aus wie ein kaputter Stift statt wie eine Maus."""
    baustein = SEITE.read_text(encoding="utf-8").split("function strichbreite", 1)[1] \
                                                .split("\n}", 1)[0]

    assert '"pen"' in baustein
    assert "return grund" in baustein, "ohne Stift muss die eingestellte Breite gelten"


def test_die_seite_erfindet_keine_druckkurve():
    """**Was hier NICHT steht, ist die Aussage.**

    Eine geglaettete Druckkurve saehe nach Handwerk aus und waere geraten: Was ein echter
    Stift auf einem echten Geraet meldet, hat in diesem Projekt niemand gemessen. Der
    Grund steht im Baustein selbst — eine Probe haelt fest, dass er dort bleibt.
    """
    text = SEITE.read_text(encoding="utf-8")
    # AB DEM ERKLAERKOMMENTAR, nicht ab der Funktionszeile: Die Begruendung steht
    # darueber, und genau sie soll hier festgehalten werden.
    mitBegruendung = text.split("/** Wie breit ein Strich", 1)[1] \
                         .split("function strichbreite", 1)[0]

    assert "gemessen" in mitBegruendung.lower()
    assert "geraten" in mitBegruendung.lower()


def test_die_tafel_bekommt_die_punktzahl_des_BILDES():
    """Eine Skizze in Bildschirmpunkten passt spaeter nicht auf das Bild, auf das sie
    gezeichnet wurde — und genau darauf soll sie angewandt werden."""
    baustein = SEITE.read_text(encoding="utf-8").split("function tafelGroesse", 1)[1] \
                                                .split("\n}", 1)[0]

    assert "naturalWidth" in baustein and "naturalHeight" in baustein


def test_der_radierer_nimmt_weg_statt_weiss_zu_malen():
    """Ein weisser Strich auf einer durchsichtigen Tafel waere weisse FARBE — er wuerde
    das Bild darunter verdecken statt die eigene Linie zu entfernen. Auf dem Bildschirm
    saehe beides zuerst gleich aus."""
    text = SEITE.read_text(encoding="utf-8")
    assert "destination-out" in text


def test_die_seite_sagt_ob_der_stift_wirklich_ankommt():
    """**Die einzige Messung, die diese Seite selbst vornimmt** — und sie misst das
    GERAET, nicht die Zeichnung.

    Steht dort "touch" statt "pen", hat der Stift nichts geliefert, was ihn von einem
    Finger unterschiede. *Eine Zeichenflaeche, die nicht sagt, ob der Stift ankommt,
    laesst den Benutzer raten, warum der Strich ueberall gleich dick ist.*
    """
    baustein = SEITE.read_text(encoding="utf-8").split("function zeigeStiftlage", 1)[1] \
                                                .split("\n}", 1)[0]

    assert "KEIN Druck" in baustein, "der Fall ohne Druck muss benannt werden"
    assert "pointerType" in SEITE.read_text(encoding="utf-8")


# ------------------------------------------- 10 · Was beim Ablegen einer Skizze gilt

def test_der_dateiname_kommt_nie_aus_dem_wunsch(server):
    """Der Wunsch kommt aus einem Browser und damit von aussen. Ihn als Dateinamen zu
    nehmen hiesse, jemand anderem zu erlauben zu bestimmen, WO geschrieben wird —
    dieselbe Luecke wie beim Lesen, nur in die andere Richtung."""
    for boese in ("../../etc/passwd", "/tmp/weg.png", "a/b.png", "x" * 300):
        name = server._skizzenname(boese)
        assert name.startswith("skizze-") and name.endswith(".png")
        assert "/" not in name and ".." not in name


def test_der_wunschname_geht_nicht_verloren_sondern_in_die_bemerkung(server):
    """*Ihn wegzuwerfen, weil er an einer Stelle unbrauchbar ist, wirft ihn auch an der
    Stelle weg, an der er etwas sagt.* Er ist das Einzige, was jemand ueber seine eigene
    Zeichnung gesagt hat."""
    assert "Variante B" in server._bemerkung("", "Variante B")
    assert "mehr Volumen" in server._bemerkung("mehr Volumen", None)


def test_eine_zu_grosse_zeichnung_wird_abgewiesen(server):
    """*Ein Riegel, der erst beim Schreiben greift, hat schon geschrieben.*

    **Diese Probe hat in ihrer ersten Fassung NICHT gefallen.** Sie verglich die
    Reihenfolge zweier Zeichenketten im Quelltext; eine Mutationsprobe hat den Riegel
    danach auf `if False` gesetzt — die Zeile stand noch da, sie tat nur nichts mehr, und
    die Probe blieb gruen.

        *Ein Waechter, der die Stellung einer Zeile prueft statt ihrer Wirkung, prueft
        den Text und nicht das Programm.*

    Jetzt wird die Entscheidung gerufen statt gelesen.
    """
    import base64 as b64

    zu_gross = b64.b64encode(
        server.PNG_KENNUNG + b"\0" * (server.SKIZZE_GROESSENRIEGEL + 1)).decode()

    with pytest.raises(server.FlaechenError) as fehler:
        server.pruefe_skizzenbytes(zu_gross)
    assert "gross" in str(fehler.value)


def test_eine_zeichnung_knapp_unter_der_grenze_kommt_durch(server):
    """Die Gegenprobe. Ohne sie waere ein Riegel, der ALLES abweist, ebenso gruen — und
    eine Flaeche, die nie eine Zeichnung annimmt, haette jede Probe bestanden."""
    import base64 as b64

    gerade_noch = server.PNG_KENNUNG + b"\0" * (server.SKIZZE_GROESSENRIEGEL
                                                - len(server.PNG_KENNUNG))
    assert server.pruefe_skizzenbytes(b64.b64encode(gerade_noch).decode()) == gerade_noch


def test_das_format_wird_am_inhalt_erkannt_und_nicht_am_namen(server):
    """Derselbe Grundsatz wie am Einlass fuer die Modelldateien: Der Name kommt von
    aussen, die Bytes sagen, was wirklich da ist.

    Ein JPEG, ein Textschnipsel, eine SVG-Datei — alle drei koennten `.png` heissen.
    """
    import base64 as b64

    for kein_png in (b"nur text", b"\xff\xd8\xff\xe0JFIF", b"<svg></svg>"):
        with pytest.raises(server.FlaechenError) as fehler:
            server.pruefe_skizzenbytes(b64.b64encode(kein_png).decode())
        assert "PNG" in str(fehler.value)


def test_kaputtes_base64_ist_eine_absage_mit_satz(server):
    """Nicht ein Absturz im Anfragebehandler. Wer einen Stacktrace liest, hoert auf."""
    with pytest.raises(server.FlaechenError):
        server.pruefe_skizzenbytes("### das ist kein base64 ###")


def test_jede_abgelegte_skizze_traegt_den_hinweis_dass_sie_nicht_gerechnet_wurde(server):
    """*Eine Bestellung, die angenommen und nicht ausgeliefert wird, ist schlimmer als
    eine abgelehnte: Die Ablehnung sieht man.*

    Angenommen wird sie trotzdem — die Zeichnung ist das, was der Mensch getan hat, und
    sie geht nicht verloren, nur weil die Maschine sie noch nicht einloesen kann.
    """
    assert "NICHT gerechnet" in server.HINWEIS_SKIZZE_OHNE_WEG
    assert "auf-20260919-123" in server.HINWEIS_SKIZZE_OHNE_WEG, (
        "der Hinweis behauptet etwas ueber die Software — dann gehoert die Messung dazu")


# ------------------------------------ 11 · Der Laufstand — zwei Sorten Lebenszeichen
#
# Die eigentliche Arbeit an dieser Klasse ist NICHT, dass etwas angezeigt wird. Sie ist,
# dass zwei verschiedene Dinge nicht gleich aussehen:
#
#   belegt    gezaehlte Diffusionsschritte — es steht fest, wie viele es werden
#   unbelegt  ein Knoten laeuft; WIE WEIT er ist, weiss niemand
#
#     Ein erfundener Balken ist dasselbe wie ein gruenes Abzeichen an einem
#     ungepruefeten Bild: Er sieht aus wie eine Auskunft und ist geraten.

def test_ein_knoten_ohne_schrittzaehler_meldet_unbelegt(server, tmp_path):
    """Ein Blender-Lauf meldet ein LEBENSzeichen. Daraus einen Anteil zu machen hiesse,
    eine Zahl zu erfinden, die niemand gemessen hat."""
    stand = server.Laufstand()
    stand.beginne(tmp_path, schritte_gesamt=8)
    stand.melde({"art": "knoten_beginnt", "knoten": "k1", "knotenart": "multipass",
                 "nummer": 1, "von": 4})

    assert stand.sicht()["art_des_zeichens"] == "unbelegt"
    assert stand.sicht()["schritt"] is None


def test_gezaehlte_schritte_melden_belegt(server, tmp_path):
    """Die Gegenprobe. Ohne sie waere ein Laufstand, der IMMER «unbelegt» sagt, ebenso
    gruen — und der einzige belegte Fortschritt dieses Projekts bliebe unsichtbar."""
    stand = server.Laufstand()
    stand.beginne(tmp_path, schritte_gesamt=8)
    stand.melde({"art": "knoten_beginnt", "knoten": "k3", "knotenart": "render",
                 "nummer": 3, "von": 4})
    stand.melde({"art": "schritt", "schritt": 5})

    sicht = stand.sicht()
    assert sicht["art_des_zeichens"] == "belegt"
    assert (sicht["schritt"], sicht["schritte_gesamt"]) == (5, 8)


def test_ohne_gesamtzahl_bleibt_es_unbelegt_auch_mit_schritten(server, tmp_path):
    """**Ein Zaehler ohne Nenner ist eine Zahl ohne Auskunft.**

    «Schritt 5» allein sagt nicht, ob es fast fertig ist oder kaum begonnen. Ein Balken
    liesse sich daraus nicht zeichnen, und ein erfundener Nenner waere geraten.
    """
    stand = server.Laufstand()
    stand.beginne(tmp_path, schritte_gesamt=None)
    stand.melde({"art": "knoten_beginnt", "knoten": "k3", "knotenart": "render",
                 "nummer": 3, "von": 4})
    stand.melde({"art": "schritt", "schritt": 5})

    assert stand.sicht()["art_des_zeichens"] == "unbelegt"


def test_der_naechste_knoten_loescht_den_alten_schrittstand(server, tmp_path):
    """Sonst stuende beim Pruefknoten noch «Schritt 8 von 8» aus der Bildstufe — eine
    Zahl aus einem anderen Knoten, und sie saehe aus wie seine eigene."""
    stand = server.Laufstand()
    stand.beginne(tmp_path, schritte_gesamt=8)
    stand.melde({"art": "knoten_beginnt", "knotenart": "render", "nummer": 3, "von": 4})
    stand.melde({"art": "schritt", "schritt": 8})
    stand.melde({"art": "knoten_beginnt", "knotenart": "qa", "nummer": 4, "von": 4})

    assert stand.sicht()["schritt"] is None
    assert stand.sicht()["art_des_zeichens"] == "unbelegt"


def test_ein_fertiger_knoten_sagt_ob_er_aus_dem_speicher_kam(server, tmp_path):
    """Der Unterschied zwischen «rechnet vier Minuten» und «kam aus dem Speicher» ist
    genau das, was ein Zuschauer sehen will."""
    stand = server.Laufstand()
    stand.beginne(tmp_path)
    stand.melde({"art": "knoten_fertig", "knoten": "k1", "knotenart": "geometrie",
                 "status": "ok", "aus_cache": True, "dauer_s": 0.0})

    assert stand.sicht()["fertige"][0]["aus_cache"] is True


def test_nach_dem_ende_laeuft_nichts_mehr_und_das_ergebnis_steht_da(server, tmp_path):
    stand = server.Laufstand()
    stand.beginne(tmp_path)
    stand.beende(ergebnis={"status": "ok", "vermerkt": 2})

    sicht = stand.sicht()
    assert sicht["laeuft"] is False
    assert sicht["knoten"] is None
    assert sicht["ergebnis"]["vermerkt"] == 2


def test_ein_gescheiterter_lauf_hinterlaesst_keinen_ewig_laufenden_stand(server, tmp_path):
    """**Der Fall, der ohne Absicht entsteht.** Eine Ausnahme in einem Hintergrundfaden
    verschwindet spurlos: Der Faden endet, und der Laufstand bliebe fuer immer auf
    «laeuft». Die Anzeige zeigte dann bis zum Neustart einen Lauf, den es nicht gibt."""
    stand = server.Laufstand()
    stand.beginne(tmp_path)
    stand.beende(fehler="Blender fehlt.")

    assert stand.sicht()["laeuft"] is False
    assert stand.sicht()["fehler"] == "Blender fehlt."


def test_der_hintergrundfaden_faengt_auch_unerwartete_fehler():
    """Er faengt ausdruecklich ALLES — und genau dafuer steht der Grund im Quelltext."""
    baustein = SERVER_PY.read_text(encoding="utf-8") \
                        .split("def _rechne_im_hintergrund", 1)[1] \
                        .split("\ndef ", 1)[0]

    assert "except Exception" in baustein
    assert "LAUFSTAND.beende" in baustein.split("except Exception", 1)[1]


def test_die_seite_zeichnet_nur_bei_gezaehlten_schritten_einen_balken():
    """**Die Auflage dieser ganzen Runde, in der Anzeige.**

    Der Balken darf nur erscheinen, wenn `art_des_zeichens` «belegt» ist. Sonst
    behauptete die Flaeche Fortschritt, wo nur Leben ist.
    """
    baustein = SEITE.read_text(encoding="utf-8").split("function zeigeLauf", 1)[1] \
                                                .split("\nasync function", 1)[0]

    assert "art_des_zeichens" in baustein
    assert 'hidden = !(f.laeuft && belegt)' in baustein


def test_die_seite_sagt_beim_unbelegten_fall_dass_sie_es_nicht_weiss():
    """Ein Puls allein koennte auch «fast fertig» heissen. Der Satz daneben sagt es."""
    baustein = SEITE.read_text(encoding="utf-8").split("function zeigeLauf", 1)[1] \
                                                .split("\nasync function", 1)[0]

    assert "WIE WEIT" in baustein and "Lebenszeichen" in baustein


def test_zwei_gleichzeitige_laeufe_werden_abgewiesen():
    """Sie schrieben beide in dieselbe Projektdatei, und der zweite ueberschriebe die
    Bilder des ersten."""
    baustein = SERVER_PY.read_text(encoding="utf-8") \
                        .split("def _rechne(self, wunsch", 1)[1] \
                        .split("\n    def ", 1)[0]

    assert 'LAUFSTAND.sicht()["laeuft"]' in baustein
    assert baustein.index("laeuft") < baustein.index("Thread")


# ------------------------------------------------- 12 · Die Tuer (Owner-Entscheid E25)
#
# Damit ein iPad herankommt, muss die Flaeche im Netz hoeren. Hier liegen Gebaeudemodelle.
# Der Owner hat am 21.09.2026 «ja, mit Kennwort» entschieden — und damit ist die
# wichtigste Eigenschaft nicht das Kennwort, sondern dass man es nicht VERGESSEN kann.

def test_ohne_kennwort_wird_im_netz_gar_nicht_erst_gebaut(server):
    """**Fail-closed, und zwar an der einzigen Stelle, an der es zaehlt.**

    *Eine Sperre, die man vergessen kann, ist im entscheidenden Augenblick vergessen.*
    """
    for adresse in ("0.0.0.0", "192.168.1.20", "::"):
        with pytest.raises(server.FlaechenError):
            server.baue_server(adresse=adresse, anschluss=0)


def test_auf_der_eigenen_maschine_bleibt_es_ohne_kennwort(server):
    """Die Gegenprobe. Auf `127.0.0.1` kommt ohnehin nur diese Maschine heran — ein
    Kennwort dort waere eine Huerde ohne Gegenueber, und wer es jeden Tag eintippt,
    schaltet es irgendwann ab."""
    srv = server.baue_server(adresse="127.0.0.1", anschluss=0)
    try:
        assert srv.RequestHandlerClass.kennwort is None
    finally:
        srv.server_close()


def test_im_netz_mit_kennwort_wird_gebaut(server):
    """Sonst waere die Probe darueber auch dann gruen, wenn gar nichts mehr gebaut wird."""
    srv = server.baue_server(adresse="0.0.0.0", anschluss=0, kennwort="geheim")
    try:
        assert srv.RequestHandlerClass.kennwort == "geheim"
    finally:
        srv.server_close()


@pytest.mark.parametrize("kopf", [
    None, "", "Bearer abc", "Basic", "Basic !!!kein-base64!!!",
])
def test_was_keine_gueltige_anmeldung_ist(server, kopf):
    """Nichts davon kommt herein — und nichts davon wirft eine Ausnahme. Ein Absturz im
    Anfragebehandler waere selbst eine Auskunft."""
    assert server.pruefe_anmeldung(kopf, "geheim") is False


def test_richtiger_benutzer_und_richtiges_kennwort_kommen_herein(server):
    import base64 as b64
    kopf = "Basic " + b64.b64encode(f"{server.BENUTZER}:geheim".encode()).decode()

    assert server.pruefe_anmeldung(kopf, "geheim") is True


def test_der_richtige_benutzer_mit_falschem_kennwort_bleibt_draussen(server):
    import base64 as b64
    kopf = "Basic " + b64.b64encode(f"{server.BENUTZER}:falsch".encode()).decode()

    assert server.pruefe_anmeldung(kopf, "geheim") is False


def test_das_richtige_kennwort_unter_falschem_namen_bleibt_draussen(server):
    """Sonst waere der Name Zierde — und eine Anmeldung, bei der die Haelfte nicht
    geprueft wird, ist eine halbe."""
    import base64 as b64
    kopf = "Basic " + b64.b64encode(f"fremd:geheim".encode()).decode()

    assert server.pruefe_anmeldung(kopf, "geheim") is False


def test_ohne_verlangtes_kennwort_kommt_jeder_herein(server):
    """`None` heisst ausdruecklich **keine Anmeldung verlangt** — der Zustand auf der
    eigenen Maschine. Es heisst NICHT «leeres Kennwort»."""
    assert server.pruefe_anmeldung(None, None) is True


def test_ein_leeres_kennwort_ist_kein_kennwort(server):
    """Wer `--kennwort ''` schreibt, hat keines gesetzt. Es als gueltig zu nehmen hiesse,
    eine Tuer zu bauen, die jeder mit der Eingabetaste oeffnet."""
    with pytest.raises(server.FlaechenError):
        server.baue_server(adresse="0.0.0.0", anschluss=0, kennwort="")


@pytest.mark.parametrize("leer", ["", "   ", "\t"])
def test_auch_die_pruefung_selbst_weist_ein_leeres_kennwort_ab(server, leer):
    """**Diese Probe gab es zuerst nicht — und eine Mutationsprobe hat das gezeigt.**

    Der Riegel hing nur an `baue_server`; `pruefe_anmeldung` las ein leeres Kennwort als
    «keine Anmeldung verlangt». Die Mutation, die genau das tut, blieb gruen, weil der
    Fall auf dem gebauten Weg nicht vorkommt.

        *Ein Riegel, der nur an einer von zwei Tueren haengt, bewacht die andere nicht.*

    Und die Richtung zaehlt: **Ein leeres Kennwort ist ein Fehler, kein Freibrief.** Die
    gefaehrlichste Abkuerzung ist die, die aus einem Fehler einen zulaessigen Zustand
    macht.
    """
    with pytest.raises(server.FlaechenError):
        server.pruefe_anmeldung("Basic Zm9vOg==", leer)


def test_verglichen_wird_in_gleichbleibender_zeit(server, monkeypatch):
    """*Ein Vergleich, dessen Dauer vom Inhalt abhaengt, verraet den Inhalt.*

    Ein gewoehnliches `==` bricht beim ersten falschen Zeichen ab. Daraus laesst sich ein
    Kennwort Zeichen fuer Zeichen erraten, ohne es je ganz zu kennen.

    **Was dieser Waechter bis zum 22.09.2026 NICHT geprueft hat, obwohl er es behauptete:**
    Er hing an drei Quelltextmerkmalen — den zwei `compare_digest`-Aufrufen und ihrer
    Reihenfolge IM TEXT. Ob beide Vergleiche auch WIRKLICH LAUFEN, hat er nie gemessen.
    Ein `if not stimmt_name: return False` zwischen den beiden Zeilen liess ihn gruen,
    und genau diese Abkuerzung ist der Angriff: Bei falschem Benutzernamen kaeme die
    Antwort frueher zurueck, und die Dauer waere wieder eine Auskunft.

        *Ein Waechter, der die Stellung einer Zeile prueft statt ihrer Wirkung, prueft
        den Text und nicht das Programm.*

    Gemessen wird darum jetzt am laufenden Aufruf: ein zaehlender Mantel um
    `hmac.compare_digest`, ein ABSICHTLICH FALSCHER Benutzername — und die Forderung,
    dass das Kennwort trotzdem verglichen wird.
    """
    import base64 as b64

    laeufe: list[tuple] = []
    echt = server.hmac.compare_digest

    def zaehlend(a, b):
        laeufe.append((a, b))
        return echt(a, b)

    monkeypatch.setattr(server.hmac, "compare_digest", zaehlend)

    kopf = "Basic " + b64.b64encode(b"fremd:geheim").decode()
    assert server.pruefe_anmeldung(kopf, "geheim") is False

    # ZWEI VERGLEICHE, obwohl schon der erste verloren war. Waere `and` eine Abkuerzung,
    # stuende hier eine Eins — und die Dauer verriete, dass der Name nicht stimmt.
    assert len(laeufe) == 2, (
        f"Bei falschem Namen liefen {len(laeufe)} Vergleiche statt zwei — dann haengt "
        f"die Dauer davon ab, welche Haelfte falsch war.")
    assert ("fremd", server.BENUTZER) in laeufe, "der Benutzername wurde nicht verglichen"
    assert ("geheim", "geheim") in laeufe, "das Kennwort wurde nicht verglichen"

    # UND DER UMGEKEHRTE FALL, damit die Zwei nicht bloss zufaellig stimmt: Auch bei
    # richtigem Namen und falschem Kennwort sind es genau zwei.
    laeufe.clear()
    kopf = "Basic " + b64.b64encode(f"{server.BENUTZER}:falsch".encode()).decode()
    assert server.pruefe_anmeldung(kopf, "geheim") is False
    assert len(laeufe) == 2


def test_das_kennwort_kommt_nicht_aus_random(server):
    """`random` erzeugt Zahlen, die fuer ein Wuerfelspiel genuegen und fuer ein Kennwort
    nicht — seine Folge laesst sich aus wenigen Werten fortrechnen.

    *Ein Zufall, der sich fortrechnen laesst, ist keiner.*
    """
    quelle = SERVER_PY.read_text(encoding="utf-8")
    assert "secrets.token_urlsafe" in quelle
    assert "import random" not in quelle

    a, b = server.erzeuge_kennwort(), server.erzeuge_kennwort()
    assert a != b and len(a) == server.KENNWORTLAENGE


class _Anfrage:
    """Eine ganze Anfrage ohne Netz — `do_GET` und `do_POST` laufen hier WIRKLICH.

    Gebraucht wird sie, weil die Tuer nur auf dem Weg zu pruefen ist, den das Produkt
    geht: Ein Browser ruft nicht `_darf_herein`, er ruft einen Pfad. Was dabei
    herauskommt, steht in `codes` (jede Antwort, in der Reihenfolge ihres Absendens), in
    `koepfe` (jede Kopfzeile) und in `rumpf` (alles, was als Rumpf auf die Leitung ging).
    """

    def __init__(self, modul, *, befehl, weg, kennwort, kopf=None, rumpf=b"",
                 ordner=None, offen=None):
        klasse = type("FlaechePruefling", (modul.Flaeche,),
                      {"kennwort": kennwort, "ordner": ordner, "kopplung_offen": offen})
        self.selbst = klasse.__new__(klasse)
        self.selbst.command = befehl
        self.selbst.path = weg
        self.selbst.headers = {"Authorization": kopf, "Content-Length": str(len(rumpf))}
        self.selbst.rfile = io.BytesIO(rumpf)
        self.selbst.wfile = io.BytesIO()
        self.codes: list[int] = []
        self.koepfe: list[tuple[str, str]] = []
        self.selbst.send_response = lambda code, *a, **k: self.codes.append(code)
        self.selbst.send_header = lambda name, wert: self.koepfe.append((name, wert))
        self.selbst.end_headers = lambda: None

    def stelle(self) -> "_Anfrage":
        (self.selbst.do_GET if self.selbst.command == "GET" else self.selbst.do_POST)()
        return self

    @property
    def rumpf(self) -> bytes:
        return self.selbst.wfile.getvalue()


# Die Wege, die ein Browser wirklich anfaesst — GET und POST, und auf beiden etwas, das
# ohne Tuer etwas HERAUSGEBEN wuerde. Keiner davon rechnet: Fiele die Tuer, antwortete
# jeder harmlos, aber er antwortete — und genau das ist hier der Befund.
_WEGE_HINTER_DER_TUER = [
    ("GET", "/"),
    ("GET", "/index.html"),
    ("GET", "/api/projekt"),
    ("GET", "/api/fortschritt"),
    ("GET", "/bild?name=bild.png"),
    ("POST", "/api/anlegen"),
    ("POST", "/api/einstellungen"),
    ("POST", "/api/verbinden"),
    ("POST", "/api/gibtesnicht"),
]


@pytest.mark.parametrize("befehl,weg", _WEGE_HINTER_DER_TUER)
def test_auch_die_seite_selbst_liegt_hinter_der_tuer(server, befehl, weg):
    """*Eine Tuer, die nur einen von zwei Wegen bewacht, ist keine Tuer.*

    Eine Anmeldung, die nur die Daten schuetzt und die Seite freigibt, schuetzt nichts —
    die Seite fragt die Daten ja gerade ab.

    **Was dieser Waechter bis zum 22.09.2026 NICHT geprueft hat:** Er las nach, ob die
    Zeichenkette `_darf_herein` in den ersten 400 Zeichen hinter `def do_GET` bzw.
    `def do_POST` VORKOMMT. Ob die Tuer dabei auch ZUHAELT, stand nirgends. Wird aus
    `if not self._darf_herein(): return` ein blosses `self._darf_herein()` — der
    Rueckgabewert verworfen, wie es bei einem Zusammenfuehren passiert —, blieb der
    Waechter gruen, und «/», «/api/projekt», «/api/fortschritt» und «/bild» gingen
    unangemeldet heraus.

        *Ein Waechter, der die Stellung einer Zeile prueft statt ihrer Wirkung, prueft
        den Text und nicht das Programm.*

    Gemessen wird jetzt die Antwort selbst: **genau eine**, und die traegt 401. Eine
    zweite Antwort hiesse, dass hinter der Tuer weitergearbeitet wurde.
    """
    a = _Anfrage(server, befehl=befehl, weg=weg, kennwort="ein-langes-kennwort").stelle()

    assert a.codes == [401], (
        f"{befehl} {weg} unangemeldet: geantwortet wurde {a.codes} statt nur 401 — "
        f"nach der 401 lief die Anfrage weiter.")
    # UND ES GING NICHTS MIT. Der Rumpf ist die eine Fehlermeldung, sonst nichts:
    # Die Seite selbst wuerde hier als HTML erscheinen. Erst als Text geprueft, damit
    # ein angehaengtes HTML als Befund faellt und nicht als geworfener JSON-Fehler.
    text = a.rumpf.decode("utf-8")
    assert "<html" not in text.lower(), f"{befehl} {weg}: hinter der 401 ging die Seite mit"
    assert json.loads(text).keys() == {"fehler"}
    # UND DER BROWSER WIRD GEFRAGT. Ohne diesen Kopf sieht der Benutzer eine
    # Fehlermeldung statt des Anmeldefensters — und kommt nie herein.
    assert any(name == "WWW-Authenticate" and wert.startswith("Basic")
               for name, wert in a.koepfe), (
        f"{befehl} {weg}: die 401 fragt nicht nach dem Kennwort — der Browser zeigt "
        f"dann kein Anmeldefenster")


def test_mit_kennwort_kommt_dieselbe_anfrage_durch(server):
    """**Die Gegenprobe, ohne die der Waechter oben auch bei einer zugemauerten Tuer
    gruen waere.** Eine Tuer, die niemanden durchlaesst, besteht jede Probe auf
    Verschlossenheit — und ist trotzdem kaputt.
    """
    import base64 as b64

    kopf = "Basic " + b64.b64encode(f"{server.BENUTZER}:geheim".encode()).decode()
    a = _Anfrage(server, befehl="GET", weg="/api/fortschritt",
                 kennwort="geheim", kopf=kopf).stelle()

    assert a.codes == [200]
    assert "laeuft" in json.loads(a.rumpf.decode("utf-8"))


def test_mit_kennwort_kommt_auch_ein_post_durch(server):
    """**Die Gegenprobe fuer die zweite Haelfte der Tuer** (Durchsicht 22.09.2026).

    Die Probe darueber deckt einen GET-Weg. Eine Tuer, die angemeldete GETs durchlaesst
    und jeden POST abweist, bestand sie — und die Flaeche waere unbenutzbar: nichts
    anlegen, nichts einstellen, nichts rechnen. Gefordert wird darum an einem POST-Weg,
    der nichts schreibt, die Antwort HINTER der Tuer: 400 (kein Ordner), nicht 401.
    """
    import base64 as b64

    kopf = "Basic " + b64.b64encode(f"{server.BENUTZER}:geheim".encode()).decode()
    a = _Anfrage(server, befehl="POST", weg="/api/anlegen",
                 kennwort="geheim", kopf=kopf, rumpf=b"{}").stelle()

    assert 401 not in a.codes, "angemeldet, und der POST wird trotzdem abgewiesen"
    assert a.codes == [400], a.codes


@pytest.mark.parametrize("befehl", ["GET", "POST"])
def test_ein_unbekannter_weg_bleibt_404_mit_seinem_satz(server, befehl):
    """**Die Wegtafel darf das Unbekannte nicht verschlucken** (Umbau 22.09.2026).

    Aus der ``if``/``elif``-Kette wurde eine Tafel. Die Gefahr einer Tafel ist eine
    andere als die der Kette: Ein Nachschlagen mit Vorgabewert (``.get(weg, "_anlegen")``)
    oder ein Fang-alles-Eintrag liesse jeden Tippfehler an einer echten Methode landen —
    und die antwortete dann mit ihrem eigenen Satz statt mit «Unbekannter Weg».

    Angemeldet angefragt, damit die 404 von der Tafel kommt und nicht von der Tuer.
    """
    import base64 as b64

    kopf = "Basic " + b64.b64encode(f"{server.BENUTZER}:geheim".encode()).decode()
    a = _Anfrage(server, befehl=befehl, weg="/api/gibtesnicht",
                 kennwort="geheim", kopf=kopf, rumpf=b"{}").stelle()

    assert a.codes == [404], a.codes
    assert json.loads(a.rumpf.decode("utf-8")) == {
        "fehler": "Unbekannter Weg: /api/gibtesnicht"}


def test_jeder_weg_der_tafel_ist_angemeldet_erreichbar(server):
    """*Ein Weg in der Tafel, dessen Methode es nicht gibt, ist ein 500 beim ersten Klick.*

    Je Eintrag eine echte Anfrage, angemeldet und **ohne** Projektordner. Keiner der Wege
    darf «Unbekannter Weg» sagen — was sie stattdessen sagen (400, 404 «kein
    Projektordner», 403 «kein Verbinden offen»), ist ihre eigene Auskunft. Gerechnet wird
    dabei nichts: ``/api/rechne`` ohne Ordner scheitert vor dem Start.
    """
    import base64 as b64

    kopf = "Basic " + b64.b64encode(f"{server.BENUTZER}:geheim".encode()).decode()
    faelle = ([("POST", w) for w in server.WEGTAFEL]
              + [("GET", w) for w in server.WEGTAFEL_LESEN if w != server.WEG_BILD]
              + [("GET", server.WEG_BILD + "?name=bild.png")])
    for befehl, weg in faelle:
        a = _Anfrage(server, befehl=befehl, weg=weg, kennwort="geheim", kopf=kopf,
                     rumpf=b"{}").stelle()
        assert len(a.codes) == 1, (befehl, weg, a.codes)
        assert "Unbekannter Weg" not in a.rumpf.decode("utf-8"), (
            f"{befehl} {weg} steht in der Tafel und antwortet trotzdem «Unbekannter Weg»")


def test_der_unverschluesselte_weg_wird_ausdruecklich_gesagt():
    """**Die unbequeme Zeile, und sie muss stehenbleiben.**

    Das Kennwort geht ueber gewoehnliches HTTP — also lesbar durch das Netz. Es haelt
    Geraete fern, die zufaellig im selben WLAN sind, und niemanden, der dort mithoert.
    Wer das nicht dazusagt, verkauft eine Sicherheit, die es nicht gibt.
    """
    quelle = SERVER_PY.read_text(encoding="utf-8")
    assert "UNVERSCHLÜSSELT" in quelle or "unverschlüsselt" in quelle
    assert "mithört" in quelle or "mitliest" in quelle


# ---------------------------------- 13 · Der Grundriss — den Standpunkt anklicken
#
# Bis zum 21.09.2026 waren `auge` und `blick_auf` ueber diese Flaeche nur als DREI
# GETIPPTE ZAHLEN erreichbar. Das ist derselbe Satz wie immer, nur von der anderen Seite:
#
#     Was nur ueber das Eintippen von Koordinaten erreichbar ist, wird nicht benutzt.

@pytest.fixture(scope="module")
def echte_glb():
    """Eine wirkliche glb aus dem Repo — keine Attrappe.

    Eine erfundene Datei wuerde hier nichts beweisen: Geprueft wird, dass die Huellbox
    des BAUWERKS gelesen wird, und dafuer muss eine Szene mit Gelaende darin vorkommen.
    """
    pfad = WURZEL / "build" / "beweis" / "02_knoten_multipass" / "szene.glb"
    if not pfad.is_file():
        pytest.skip("Die Beweis-glb liegt nicht im Arbeitsbaum.")
    return pfad


def test_der_grundriss_liest_die_huellbox_des_bauwerks(server, echte_glb):
    """Ohne Blender, hier, in Sekundenbruchteilen — und in Weltkoordinaten mit Z oben."""
    g = server.grundriss(str(echte_glb), "Y")

    assert g["bbox"] is not None, g["grund"]
    (x0, y0, z0), (x1, y1, z1) = g["bbox"]
    assert x1 > x0 and y1 > y0 and z1 > z0


def test_das_gelaende_wird_wirklich_abgezogen(server, echte_glb):
    """**Die Probe, ohne die der Grundriss eine Wiese zeigen koennte.**

    Faellt die Software auf die Szenenbox zurueck, ist das Bauwerk darin ein Fleck — und
    ein Standpunkt, den jemand darin anklickt, sieht am Haus vorbei. `schrumpfung` ist
    die Zahl, an der sich ablesen laesst, ob die Gelaenderegel ueberhaupt gegriffen hat.
    """
    from aiimaging import glbbox

    g = server.grundriss(str(echte_glb), "Y")
    roh = glbbox.bauwerksbox(str(echte_glb), up_axis="Y")

    assert roh["schrumpfung"] > 0.1, (
        f"Die Gelaenderegel hat nur um {roh['schrumpfung']:.3f} verkleinert — dann ist "
        f"diese Probe an einer Szene gefahren, in der es nichts zu trennen gibt.")

    # UND JETZT DIE EIGENTLICHE FRAGE, und sie hat in der ersten Fassung gefehlt: Es
    # genuegt nicht, dass die Regel GEGRIFFEN hat — zurueckkommen muss ihr Ergebnis.
    #
    # Eine Mutationsprobe hat genau das gezeigt: Ein Rueckfall auf die Szenenbox blieb
    # gruen, weil die alte Fassung nur `schrumpfung` las — eine Zahl NEBEN der Box.
    #
    #     *Ein Waechter, der eine Kennzahl prueft statt des Werts, den sie beschreibt,
    #     bewacht die Beschreibung.*
    assert g["bbox"] == roh["bbox_bauwerk"]
    szene = roh["bbox_szene"]
    breite_bau = g["bbox"][1][0] - g["bbox"][0][0]
    breite_szene = szene[1][0] - szene[0][0]
    assert breite_bau < breite_szene, (
        "Der Grundriss ist so breit wie die ganze Szene — dann steht dort das Gelaende, "
        "und ein Standpunkt darin sieht am Haus vorbei.")


def test_ohne_hochachse_gibt_es_keinen_grundriss_und_einen_grund(server, echte_glb):
    """Eine leere Flaeche ohne Grund saehe aus wie ein Fehler der Anzeige."""
    g = server.grundriss(str(echte_glb), None)

    assert g["bbox"] is None
    assert "up_axis" in g["grund"]


def test_fuer_Z_up_wird_nicht_geraten(server, echte_glb):
    """Die Bibliothek weigert sich, und ihr Satz kommt unveraendert durch. *Eine geratene
    Achsenkonvention waere der vierte unvereinbare Vertrag in diesem Projekt.*"""
    g = server.grundriss(str(echte_glb), "Z")

    assert g["bbox"] is None
    assert g["grund"], "die Weigerung ohne Begruendung waere schlimmer als keine"


def test_ohne_geometrie_sagt_es_das(server):
    g = server.grundriss(None, "Y")

    assert g["bbox"] is None and "Geometrie" in g["grund"]


def test_eine_unlesbare_glb_stuerzt_nicht_ab(server, tmp_path):
    """Sie kommt als Satz zurueck. Ein Absturz im Anfragebehandler naehme der Seite auch
    alles andere weg — die Bilder, den Knotenbaum, die Skizzen."""
    g = server.grundriss(str(tmp_path / "gibt-es-nicht.glb"), "Y")

    assert g["bbox"] is None and g["grund"]


def test_der_riss_rechnet_in_beiden_richtungen_mit_demselben_massstab():
    """Ein Grundriss, der X anders skaliert als Y, zeigt ein Haus, das es nicht gibt —
    und ein Standpunkt daraus staende anderswo als geklickt."""
    baustein = SEITE.read_text(encoding="utf-8").split("function rissAbbildung", 1)[1] \
                                                .split("\nfunction ", 1)[0]

    assert baustein.count("massstab") >= 3
    assert "Math.max(breite, tiefe)" in baustein, "sonst zwei Massstaebe"
    # UND DIE FLAECHE MUSS AUCH HINEINPASSEN. `c.width` allein zeichnet bei einem
    # breiteren als hohen Feld ueber den unteren Rand hinaus — der Standpunkt waere dort
    # anklickbar, wo nichts zu sehen ist.
    assert "Math.min(c.width, c.height)" in baustein


def test_norden_zeigt_nach_oben():
    """Auf einer Leinwand waechst y nach unten. Ohne das Minus staende Norden unten — und
    jeder Standpunkt waere an der Nordseite, wenn er an der Suedseite gemeint war."""
    baustein = SEITE.read_text(encoding="utf-8").split("function rissAbbildung", 1)[1] \
                                                .split("\nfunction ", 1)[0]

    assert "c.height / 2 - (y - my)" in baustein


def test_das_blickziel_liegt_auf_halber_hoehe_und_nicht_am_boden():
    """Wer auf den Boden zielt, bekommt ein Bild, in dem das Haus nach hinten kippt."""
    baustein = SEITE.read_text(encoding="utf-8").split("async function rissUebernehmen", 1)[1] \
                                                .split("\n}", 1)[0]

    assert "mitte" in baustein and "riss.bbox[1][2]" in baustein


def test_der_standpunkt_nimmt_denselben_weg_wie_jede_andere_einstellung():
    """*Zwei Wege, dieselbe Sache, und einer davon veraltet.*

    Der Grundriss schreibt `auge` und `blick_auf` ueber dieselbe Funktion wie die
    Eingabefelder — also auch durch dieselbe Pruefung der Bibliothek.
    """
    text = SEITE.read_text(encoding="utf-8")
    baustein = text.split("async function rissUebernehmen", 1)[1].split("\n}", 1)[0]

    assert "einstellungenSchicken" in baustein
    assert text.count("/api/einstellungen") == 1, "es gibt genau einen Weg dorthin"


def test_ohne_bauwerksbox_wird_NICHT_auf_die_szenenbox_ausgewichen(server, monkeypatch,
                                                                   echte_glb):
    """**Der Fall, den die Proben oben nicht betreten** — und eine Mutationsprobe hat es
    gezeigt: Ein Rueckfall auf die Szenenbox blieb gruen, weil in der Beweis-Szene immer
    eine Bauwerksbox herauskommt.

    Findet die Gelaenderegel nichts, ist die Szenenbox das Naechstliegende und das
    Falscheste: Sie enthaelt das Gelaende. Ein Grundriss, in dem das Haus ein Fleck in
    einer Wiese ist, laedt zu einem Standpunkt ein, der daran vorbeisieht.

        *Die naheliegendste Ersatzantwort ist die, die niemand als Ersatz erkennt.*
    """
    from aiimaging import glbbox

    monkeypatch.setattr(glbbox, "bauwerksbox", lambda *a, **k: {
        "bbox_bauwerk": None,
        "bbox_szene": [[-100.0, -100.0, 0.0], [100.0, 100.0, 5.0]],
        "note": "Die Regel hat nichts gefunden.",
        "schrumpfung": 0.0,
    })

    g = server.grundriss(str(echte_glb), "Y")

    assert g["bbox"] is None, "die Szenenbox ist hier keine Antwort"
    assert g["grund"], "und das Schweigen darueber waere schlimmer als die falsche Box"
