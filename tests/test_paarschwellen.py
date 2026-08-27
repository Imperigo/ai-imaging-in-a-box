"""Die Trennkurve — und vor allem die Lagen, in denen sie schweigen muss.

Der teuerste Fehler dieses Moduls wäre nicht eine falsche Zahl, sondern eine Tabelle,
die perfekt aussieht, weil eine der beiden Gruppen leer war. Genau darauf zielt die
Mehrzahl dieser Tests.
"""

import pytest

from aiimaging import paarschwellen


def _fall(fid, gut, wert, szene="s1", kamera="k1"):
    return {"fall_id": fid, "gut": gut, "wert": wert, "szene": szene, "kamera": kamera}


def _volle_menge(gut_werte, schlecht_werte):
    """Genug Fälle, Szenen und Kameras, damit keine Umfangs-Vorbehalte dazwischenreden."""
    faelle = []
    for i, w in enumerate(gut_werte):
        faelle.append(_fall(f"g{i}", True, w, szene=f"s{i % 3}", kamera=f"k{i % 2}"))
    for i, w in enumerate(schlecht_werte):
        faelle.append(_fall(f"b{i}", False, w, szene=f"s{i % 3}", kamera=f"k{i % 2}"))
    return faelle


# ======================================================================================
# Die Rechnung selbst
# ======================================================================================

def test_beide_fehlerarten_werden_getrennt_gezaehlt():
    """Eine Schwelle mitten zwischen zwei sich überlappenden Gruppen macht beide Fehler."""
    faelle = _volle_menge([0.9] * 20, [0.5] * 20)
    kurve = paarschwellen.trennkurve(faelle, (0.6,))
    punkt = kurve["punkte"][0]
    assert punkt["falsch_bestanden"] == 0      # kein schlechter Fall liegt über 0.6
    assert punkt["falsch_gesperrt"] == 0       # kein guter Fall liegt darunter
    assert punkt["richtig_bestanden"] == 20
    assert punkt["richtig_gesperrt"] == 20


def test_die_schwelle_ist_einschliesslich():
    """`wert >= schwelle` besteht. Ein Fall GENAU auf der Schwelle geht durch."""
    faelle = _volle_menge([0.8] * 20, [0.8] * 20)
    punkt = paarschwellen.trennkurve(faelle, (0.8,))["punkte"][0]
    assert punkt["falsch_bestanden"] == 20, "ein schlechter Fall auf der Schwelle geht durch"
    assert punkt["falsch_gesperrt"] == 0, "ein guter Fall auf der Schwelle wird nicht gesperrt"


def test_eine_saubere_trennung_nennt_ihr_intervall():
    faelle = _volle_menge([0.9] * 20, [0.3] * 20)
    kurve = paarschwellen.trennkurve(faelle)
    assert kurve["trennt_sauber"] is True
    assert kurve["sauber_zwischen"] == (0.3, 0.9)
    assert kurve["genuegt_als_kalibrierung"] is True


def test_eine_ueberlappung_wird_als_solche_gemeldet():
    """Ein einziger schlechter Fall über dem schlechtesten guten reicht."""
    faelle = _volle_menge([0.9] * 19 + [0.4], [0.3] * 19 + [0.5])
    kurve = paarschwellen.trennkurve(faelle)
    assert kurve["trennt_sauber"] is False
    assert kurve["sauber_zwischen"] is None
    assert kurve["niedrigster_guter"] == 0.4
    assert kurve["hoechster_schlechter"] == 0.5


# ======================================================================================
# Die dritte Antwort — hier verdient sie ihren Namen
# ======================================================================================

def test_ohne_schlechte_faelle_ist_die_trennung_NICHT_BEURTEILBAR():
    """**Der Kern dieses Moduls.**

    Ohne schlechte Fälle sperrt jede Schwelle nur richtig. Die Tabelle sähe perfekt
    aus — und `trennt_sauber` müsste `True` sagen, wenn man sie rechnen liesse. Sie sagt
    `None`, und der Grund steht dabei.
    """
    faelle = _volle_menge([0.9] * 20, [])
    kurve = paarschwellen.trennkurve(faelle)
    assert kurve["trennt_sauber"] is None, "nicht False und schon gar nicht True"
    assert kurve["sauber_zwischen"] is None
    assert any("KEIN EINZIGER MESSBARER SCHLECHTER FALL" in v for v in kurve["vorbehalte"])
    assert kurve["genuegt_als_kalibrierung"] is False


def test_ohne_gute_faelle_ebenso():
    kurve = paarschwellen.trennkurve(_volle_menge([], [0.3] * 20))
    assert kurve["trennt_sauber"] is None
    assert any("KEIN EINZIGER MESSBARER GUTER FALL" in v for v in kurve["vorbehalte"])


def test_eine_leere_menge_bringt_das_modul_nicht_zu_fall():
    """Kein `max()` auf einer leeren Sammlung, kein freundliches `all()`."""
    kurve = paarschwellen.trennkurve([])
    assert kurve["trennt_sauber"] is None
    assert len(kurve["punkte"]) == len(paarschwellen.KANDIDATEN_RHO)
    assert all(p["falsch_bestanden"] == 0 for p in kurve["punkte"])
    assert len(kurve["vorbehalte"]) >= 2


def test_ein_nicht_messbarer_fall_wird_benannt_statt_verworfen():
    """Er zählt in keiner Spalte — aber er steht namentlich da."""
    faelle = _volle_menge([0.9] * 20, [0.3] * 20)
    faelle.append(_fall("stumm", False, None))
    kurve = paarschwellen.trennkurve(faelle)
    assert kurve["nicht_messbar"] == ["stumm"]
    assert kurve["n_schlecht"] == 21, "er wird mitgezählt"
    assert kurve["n_schlecht_messbar"] == 20, "aber nicht eingerechnet"
    assert any("NICHT MESSBAR" in v for v in kurve["vorbehalte"])
    assert kurve["genuegt_als_kalibrierung"] is False


# ======================================================================================
# Der Umfang — das Problem, das dieses Modul lösen soll, wird nicht neu aufgelegt
# ======================================================================================

def test_sieben_faelle_aus_einer_szene_genuegen_nicht():
    """Genau die Lage, aus der `PAAR_RHO_SCHWELLE = 0.80` stammt."""
    faelle = ([_fall(f"g{i}", True, 0.9) for i in range(4)]
              + [_fall(f"b{i}", False, 0.3) for i in range(3)])
    kurve = paarschwellen.trennkurve(faelle)
    assert kurve["trennt_sauber"] is True, "sie trennen — nur heisst das hier nichts"
    assert kurve["genuegt_als_kalibrierung"] is False
    assert any("UMFANG UNTER DEM MINDESTMASS" in v for v in kurve["vorbehalte"])
    assert any("ZU WENIG STREUUNG" in v for v in kurve["vorbehalte"])


def test_eine_szene_reicht_nicht_auch_bei_vollem_umfang():
    """Beide Masse hängen an der Maskenlage — der Bodenanteil entscheidet mit."""
    faelle = ([_fall(f"g{i}", True, 0.9, szene="nur_eine", kamera=f"k{i % 2}")
               for i in range(20)]
              + [_fall(f"b{i}", False, 0.3, szene="nur_eine", kamera=f"k{i % 2}")
                 for i in range(20)])
    kurve = paarschwellen.trennkurve(faelle)
    assert kurve["genuegt_als_kalibrierung"] is False
    assert any("ZU WENIG STREUUNG" in v for v in kurve["vorbehalte"])


def test_ohne_vorbehalte_genuegt_die_kurve():
    """Die Gegenprobe: Erfüllt eine Menge alle Bedingungen, meldet das Modul nichts."""
    kurve = paarschwellen.trennkurve(_volle_menge([0.9] * 20, [0.3] * 20))
    assert kurve["vorbehalte"] == []
    assert kurve["genuegt_als_kalibrierung"] is True


# ======================================================================================
# Ein Fall ohne Etikett ist ein Fehler, kein übersprungener Datensatz
# ======================================================================================

def test_ein_fall_ohne_etikett_wird_abgewiesen():
    with pytest.raises(paarschwellen.PaarschwellenError, match="gut oder schlecht"):
        paarschwellen.trennkurve([{"fall_id": "x", "wert": 0.5}])


def test_ein_fall_ohne_kennung_wird_abgewiesen():
    with pytest.raises(paarschwellen.PaarschwellenError, match="keine Kennung"):
        paarschwellen.trennkurve([{"gut": True, "wert": 0.5}])


def test_die_null_ist_ein_gueltiges_etikett_und_keine_fehlende_angabe():
    """`gut=False` darf nicht mit «fehlt» verwechselt werden."""
    kurve = paarschwellen.trennkurve([_fall("b0", False, 0.3)])
    assert kurve["n_schlecht"] == 1


# ======================================================================================
# Die Kandidatenreihen
# ======================================================================================

def test_die_rho_reihe_beginnt_bei_null():
    """Bei 0.80 zu beginnen hiesse, die Antwort schon zu kennen."""
    assert paarschwellen.KANDIDATEN_RHO[0] == 0.0
    assert paarschwellen.KANDIDATEN_RHO[-1] == 0.95


def test_die_kantenanteil_reihe_endet_unter_dem_perfekten_bild():
    """Das perfekte Bild erreicht 87,4 % — eine Schwelle darüber wäre ein Verbot."""
    assert paarschwellen.KANDIDATEN_KANTENANTEIL[-1] == 0.90
    assert max(paarschwellen.KANDIDATEN_KANTENANTEIL) < 0.95


def test_die_heutigen_schwellen_liegen_in_ihren_reihen():
    """Sonst kann die Kurve nicht sagen, was die heutige Zahl kostet."""
    from aiimaging import geometrie_qa
    assert geometrie_qa.PAAR_RHO_SCHWELLE in paarschwellen.KANDIDATEN_RHO
    assert geometrie_qa.PAAR_KANTENANTEIL_SCHWELLE in paarschwellen.KANDIDATEN_KANTENANTEIL


# ======================================================================================
# Der Bericht
# ======================================================================================

def test_der_bericht_stellt_den_vorbehalt_vor_die_zahlen():
    """Eine Einschränkung nach der Tabelle wird nicht mehr gelesen."""
    text = paarschwellen.bericht(paarschwellen.trennkurve(_volle_menge([0.9] * 20, [])))
    ort_vorbehalt = text.index("KEIN EINZIGER MESSBARER SCHLECHTER FALL")
    ort_tabelle = text.index("Schwelle | falsch bestanden")
    assert ort_vorbehalt < ort_tabelle


def test_der_bericht_empfiehlt_nichts():
    text = paarschwellen.bericht(paarschwellen.trennkurve(_volle_menge([0.9] * 20,
                                                                      [0.3] * 20)))
    assert "KEINE EMPFEHLUNG" in text
    assert "Entscheidung und keine Messung" in text


def test_der_bericht_nennt_die_ueberlappung_mit_beiden_zahlen():
    kurve = paarschwellen.trennkurve(_volle_menge([0.9] * 19 + [0.4], [0.3] * 19 + [0.5]))
    text = paarschwellen.bericht(kurve)
    assert "ÜBERLAPPEND" in text
    assert "0.4000" in text and "0.5000" in text


def test_der_bericht_sagt_nicht_beurteilbar_statt_sauber():
    text = paarschwellen.bericht(paarschwellen.trennkurve([]))
    assert "NICHT BEURTEILBAR" in text
    assert "SAUBER" not in text


# ======================================================================================
# Der Einstieg — damit die Fähigkeit nicht nur über Tests erreichbar ist
# ======================================================================================

def _werkzeug():
    """`tools/paarschwellen.py` als Modul — es liegt nicht im Paket."""
    import importlib.util
    from pathlib import Path
    pfad = Path(__file__).resolve().parents[1] / "tools" / "paarschwellen.py"
    spec = importlib.util.spec_from_file_location("werkzeug_paarschwellen", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _schreibe(tmp_path, faelle):
    import json
    p = tmp_path / "faelle.json"
    p.write_text(json.dumps(faelle), encoding="utf-8")
    return p


def test_das_werkzeug_scheitert_wenn_die_kurve_keine_kalibrierung_ist(tmp_path, capsys):
    """Rückgabewert 1 — und die Tabelle wird trotzdem gedruckt."""
    w = _werkzeug()
    pfad = _schreibe(tmp_path, [_fall("g0", True, 0.9), _fall("b0", False, 0.3)])
    assert w.main([str(pfad)]) == 1
    assert "UMFANG UNTER DEM MINDESTMASS" in capsys.readouterr().out


def test_das_werkzeug_gibt_null_zurueck_wenn_die_kurve_traegt(tmp_path):
    w = _werkzeug()
    pfad = _schreibe(tmp_path, _volle_menge([0.9] * 20, [0.3] * 20))
    assert w.main([str(pfad)]) == 0


def test_das_werkzeug_nimmt_auch_einen_satz_mit_schluessel_faelle(tmp_path):
    import json
    w = _werkzeug()
    p = tmp_path / "f.json"
    p.write_text(json.dumps({"faelle": _volle_menge([0.9] * 20, [0.3] * 20)}),
                 encoding="utf-8")
    assert w.main([str(p)]) == 0


def test_das_werkzeug_waehlt_die_reihe_nach_der_groesse(tmp_path, capsys):
    """Die beiden Reihen sind verschieden lang — sonst wären die Tabellen verwechselbar."""
    w = _werkzeug()
    pfad = _schreibe(tmp_path, _volle_menge([0.9] * 20, [0.3] * 20))
    w.main([str(pfad), "--groesse", "kantenanteil"])
    text = capsys.readouterr().out
    assert "kantenanteil" in text
    assert "0.95" not in text, "die Kantenanteil-Reihe endet bei 0.90"


def test_das_werkzeug_meldet_einen_fall_ohne_etikett_statt_ihn_zu_ueberspringen(tmp_path):
    w = _werkzeug()
    import json
    p = tmp_path / "f.json"
    p.write_text(json.dumps([{"fall_id": "x", "wert": 0.5}]), encoding="utf-8")
    assert w.main([str(p)]) == 2
