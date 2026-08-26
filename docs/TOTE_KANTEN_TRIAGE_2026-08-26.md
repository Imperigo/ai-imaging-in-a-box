# Triage der toten Kanten — 26.08.2026

`tools/tote_kanten.py` meldet **80 öffentliche Funktionen ohne Aufrufer**: 79 davon
erreicht nur die Testsammlung, eine erreicht niemand. Das Werkzeug entstand am selben Tag,
und sein eigener Schlusssatz sagt, was danach zu tun ist:

> *Wer eine Meldung prüft, sucht den Aufrufer selbst. Eine Meldung ist der ANFANG einer
> Untersuchung und kein Urteil.*

Dieses Dokument ist diese Untersuchung. **Alle 80 haben ein Urteil**, keine ist übergangen.

---

## Warum das nicht warten konnte

Diese Woche trägt **acht** tote Kanten, und die achte war die teuerste: Der `torwaechter`
— der Riegel gegen Massstabsfehler, gebaut, geprüft, mit einem Docstring, der den Anlass
in drei Absätzen begründet — lief auf dem Weg, der Bilder erzeugt, **nirgends**.
`grep -c torwaechter` über `abholer.py`, `bruecke.py` und `tools/abholen.py` ergab
**0, 0, 0**.

*Gerade seine gute Begründung liess ihn für angeschlossen halten.* Eine Liste von 80
weiteren Kandidaten ohne Urteil ist darum kein Fortschritt, sondern eine Einladung, beim
nächsten Mal wieder wegzusehen.

## Wie geurteilt wurde

Für jeden Namen wurde gesucht, **was stattdessen läuft**. Das ist die Frage, die trägt:
Eine ungerufene Funktion neben einer gerufenen Geschwisterfunktion ist etwas anderes als
eine ungerufene Funktion, deren Aufgabe niemand erledigt.

Zwei Grenzen des Werkzeugs, beide bekannt und beide hier mitgedacht:

* Es löst über den **blossen Namen** auf, nicht über den Import — `foo.bar()` und
  `baz.bar()` sehen gleich aus. Es meldet darum eher zu wenig als zu viel.
* `runners/`, `mcp_server.py` und `mcp_schemas.py` gelten als Aussenkante und sind
  Einstiegspunkte, keine toten Kanten.

---

## A · Studie und Kalibrierung — 23 Namen, zu Recht ungerufen

| Modul | Namen | wozu es einmal lief |
|---|---:|---|
| `stilstudie.py` | 13 | Herleitung von `stil_qa.SCHWELLE_STIL`; die Schwelle steht seit 18.08. auf 0,666, **abgeleitet statt gesetzt**, gemessen an 4950 Paaren |
| `schwellenstudie.py` | 5 | Herleitung von `geometrie_qa.SCHWELLE_GEOMETRIE`; Ergebnis in `docs/SCHWELLENSTUDIE_2026-08-18.md` |
| `varianten.py` | 5 | Ab wann ein Unterschied zwischen zwei Bildern einer ist — die Absage an den geerbten Variantenbewerter |

**Urteil: kein Handlungsbedarf, aber auch kein Löschen.** Eine Studie ist Beleg der
Vertiefungsarbeit: Sie muss nachvollziehbar bleiben, damit die Zahl, die sie hervorgebracht
hat, verteidigbar bleibt. *Eine gelöschte Herleitung macht aus einer abgeleiteten Schwelle
wieder eine gesetzte.*

Diese 23 sind der Grund, warum das Werkzeug **meldet und nicht prüft** (Entscheid 19 vom
26.08.): Ein Test darauf wären 23 Fehlalarme, und der erste schaltet ihn ab.

---

## B · Fähigkeit für eine Phase, die nicht läuft — 19 Namen

| Modul | Namen | worauf sie wartet |
|---|---:|---|
| `kosmo_naht.py` | 6 | die MCP-Registrierung bei KosmoOrbit; sie ist **nicht ausgeführt**, und das steht so im README |
| `herkunft.py` | 5 | Phase 4, „Connectors: ArchiCAD über IFC4, Rhino über glTF" |
| `lora.py` | 4 | Phase 4, LoRA-Stiltraining — **nie ein Training ausgeführt**, im README so vermerkt |
| `kette.py` | 2 | der Graph-Umbau; gebaut und gemessen, aber auf dem Stand vor sechs Tagen intensiver Entwicklung |
| `konversionstreue.py` | 2 | `auf-20260824-39`, unbeantwortet — misst, ob die Konversion nicht nur *durchläuft* |

**Urteil: die Lücke ist an anderer Stelle bereits benannt.** Für jede dieser fünf steht
im README, im `PLAN.md` oder in einem offenen Auftrag, dass sie nicht läuft. *Das ist der
Unterschied zum `torwaechter`: Der galt als angeschlossen.*

Eine Ausnahme mit eigenem Gewicht: `kosmo_naht.satz_ist_freigegeben_laut_status` ist die
**einzige** der 80, die auch kein Test nennt. Sie ist am 26.08. geprüft worden (Commit
«Zwei Freigabewege, und nur einer wird benutzt») — *ungeprüft ist schlimmer als ungerufen.*

---

## C · Bewusst anders gelöst — 27 Namen

Die interessanteste Gruppe: Hier gibt es eine Geschwisterfunktion, die läuft, und der
Unterschied zwischen beiden ist jedes Mal eine **Entscheidung**.

| ungerufen | was stattdessen läuft | warum das die bessere Wahl ist |
|---|---|---|
| `stil_qa.stil_gate` und 5 weitere | `abholer._stil_urteil_aus_belichtung` | Owner-Entscheid 21.08.: Der Hausstil ist **fest formuliert**, geprüft wird gegen einen gemessenen Belichtungsrahmen. Ein Referenzsatz, gegen den `stil_gate` misst, existiert nicht — und fremde Bilder dürfen es nicht sein |
| `geometrie_qa.anker_fuer` | `abholer._nullprobe` | Der Pfad **misst** den Nullanker dieser Szene, statt ihn aus `NULLANKER` nachzuschlagen. Eine Zahl gehört an die Bedingung, unter der sie gemessen wurde |
| `geometrie_qa.erreichbarkeit_fuer` | `abholer._erreichbarkeit_dieser_szene` | dasselbe: die Obergrenze **dieses Laufs** statt einer Tabellenzeile aus `IOU_DECKEL` |
| `geometrie_qa.polaritaet_aus_messungen`, `anteil_naeher_am_rand` | — | Kalibrier- und Diagnosewerkzeug, gehört sachlich zu Gruppe A |
| `gate.gesamturteil`, `als_kosmovis_verdikt` | `kosmo_szene.als_ergebnis` | **siehe unten — die einzige Doppelung dieser Gruppe** |
| `kosmo_szene.kamera_zu_spec`, `brennweite_zu_fov`, `backbone_nach_fremd` | `spec_zu_kamera`, `fov_zu_brennweite`, `backbone_von_fremd` | Die **Rückrichtung** der Naht. Wir *empfangen* Aufträge von KosmoOrbit und stellen keine — der Weg, auf dem sie liefe, existiert nicht |
| `bildlesen.tiefen_aus_png`, `png_befund`, `exr_kopf` | `tiefen_aus_report`, `pruefe_png` | Die Tiefe kommt aus dem Bericht mit ihrer Normalisierung, nicht aus dem PNG allein; die beiden anderen sind Diagnose |
| `prompts.komponiere`, `baustein`, `uebersicht` | roher Prompt aus dem fremden Vertrag | **In `abholer.negativ_lage` ausdrücklich protokolliert**, samt Begründung, warum ein Anschluss heute den schlechtesten Zustand ergäbe |
| `fortschritt.beobachte`, `wache_fuer_status` | `abholer`s eigene Wache auf dem Ausgabeordner | Entscheid 20 vom 26.08.: **geprüft statt gelöscht** |
| `jobs.freigeben`, `liste_jobs` | — | liegt beim Owner: wer eine GPU freigeben darf, ist keine Entscheidung des Codes |
| `contracts.load_render_scene` | `bruecke` liest die Datei selbst, `validate_render_scene` prüft sie | kleine Doppelung, ohne Folgen |
| `bildschreiben.schreibe_farb_png` | `schreibe_png` | Farbe schreibt heute niemand |

### Die eine Doppelung, die eine Entscheidung verdient

`gate.py` heisst **DAS DOPPEL-GATE**, und sein Docstring trägt den Anlass der ganzen
Arbeit:

> *Im Vorläufer KosmoVis lief eine Zeit lang nur das Stil-Gate. Bei einem Lauf an echter
> Geometrie meldete es `bestanden` mit einem Stil-Score von 0.42 — auf einen Render, dessen
> Kubatur halluziniert war.*

Auf dem Produktpfad ruft es niemand. Das UND bildet `kosmo_szene.als_ergebnis` selbst:

```python
messbar = [x for x in (geo_ok, stil_ok) if x is not None]
bestanden = bool(messbar) and all(messbar)
```

**Nachgerechnet, nicht vermutet:** Die beiden Fassungen urteilen in jedem Fall gleich, der
wirklich vorkommt. `gate.py` ist *fail-closed* — fehlt `bestanden`, gilt nicht bestanden;
`als_ergebnis` lässt ein `None` aus dem UND herausfallen. Der Unterschied griffe nur, wenn
ein Stilurteil fehlte, **und genau dann fehlt es nur, wenn kein Stil bestellt war**. Wurde
einer bestellt und nicht gemessen, setzt `als_ergebnis` `passed: false` — ebenfalls
fail-closed (`kosmo_szene.py:719`).

*Es ist also keine Lücke, sondern zwei Fassungen derselben zentralen Entscheidung.* Und
das ist dieselbe Fehlerart wie ein Lexikoneintrag, der zweimal dasteht: Eine der beiden
veraltet, und wer die falsche liest, liest die alte. **Der Anschluss ist aber kein
Aufräumen** — er änderte das Verhalten im Fall *«kein Stil bestellt»* von *bestanden* auf
*nicht bestanden*, und das ist eine Vertragsänderung. Sie gehört entschieden und nicht
nebenbei gemacht.

---

## D · Offen — 11 Namen, drei Fäden

### D.1 · Der Kamerasatz wird nie als Satz beurteilt (`komposition.py`, 7)

`beurteile_kamera` und `beurteile_bericht` laufen. **`beurteile_kamerasatz` — „den ganzen
Kamerasatz gegen das Regelwissen halten" — nicht.** Die sechs übrigen
(`bildanteile`, `deckenanteil`, `bodenanteil_erreichbar`, `hoehe_fuer_bild_gleichgewicht`,
`horizont_verschiebung_pp`, `kleinbild_aequivalent`) sind seine Rechenteile und fallen mit
ihm.

Das ist mehr als eine ungenutzte Funktion: **Am 26.08. wurde eine Satzfrage ad hoc gelöst**
— die doppelte Ansicht, bei der `sSE` und `nNW` an einem Quader bytegleich sind. Die Lösung
sitzt im `abholer` und nicht in `komposition`, wo das Regelwissen liegt.

*Zu prüfen wäre, ob `beurteile_kamerasatz` die Frage schon beantwortet, die im Abholer neu
gebaut wurde.* Das ist der stärkste Kandidat auf die neunte tote Kante.

### D.2 · Die Bibliothek kann das Auftragsformat nicht mehr bauen (`auftrag.py`, 3)

`baue_auftrag`, `schreibe_auftrag` und `neue_auftrag_id` haben keinen Aufrufer — Aufträge
entstehen von Hand. Das allein wäre harmlos. **Gemessen an den Dateien im Repo ist es das
nicht:**

| | Aufträge in `auftraege/offen/` |
|---|---:|
| mit einem Feld `anweisung` | **4** (alle vom 26.08.) |
| ohne | **42** |

`CLAUDE.md` verlangt seit dem **22.08.2026**: *„Was der Worker wissen muss, steht in der
Auftragsdatei."* Aus derselben Regel stammt das Pflichtfeld `worker` — **und das ist in
`pruefe_auftrag` gelandet, die Anweisung nicht.** Halb im Code, halb nur im Text.

Vier Aufträge sind seither ohne das Feld hinausgegangen (`auf-38` bis `auf-41`). Sie tragen
ihre Anweisung im Fliesstext von `beschreibung` — *inhaltlich* also erfüllt, aber an einer
Stelle, auf die sich kein Leser verlassen kann. **Eine Hausregel ohne Wächter ist eine
Bitte.**

### D.3 · Verdeckte Sicht wird nie freigezogen (`kameras.py`, 1)

`schiebe_bis_im_bild` läuft — die Kamera rückt zurück, bis das Bauwerk ins Bild passt.
`ziehe_bis_frei` — *„zieht die Kamera heran, solange etwas die Sicht verstellt"* — läuft
nicht. **Verdeckung wird auf dem Produktpfad also nicht behandelt.**

Ob sie behandelt werden muss, ist eine Messfrage und keine Meinung: An einem freistehenden
Testbau verdeckt nichts. An einem Modell mit Gelände und Umgebung — genau der Sorte, die
zwei der 40 echten Dateien mit 1002 m und 1127 m Ausdehnung sind — sehr wohl.

---

## Was daraus folgt

1. **D.2 wird sofort geschlossen** — ein Wächter über `auftraege/offen/`, der jede
   Auftragsdatei ab dem 22.08.2026 auf ihre Pflichtfelder prüft. Billig, maschinell
   entscheidbar, und er beisst beim nächsten von Hand geschriebenen Auftrag.
2. **D.1 und D.3 werden gemessen, nicht geraten.** Ob `beurteile_kamerasatz` die Doppelansicht
   schon beantwortet, steht in seinem Code; ob Verdeckung vorkommt, steht nur in echten
   Modellen — und die hat die HomeStation.
3. **Die Doppelung in `gate.py` wird dem Owner vorgelegt**, weil ihr Anschluss den Vertrag
   ändert.

## Was daraus ausdrücklich nicht folgt

**Keine Löschung.** Keine der 80 wird entfernt. Für A ist die Nachvollziehbarkeit der Zweck,
für B ist die Phase nur noch nicht dran, und in C ist jede einzelne eine dokumentierte
Entscheidung. *Über Löschen entscheidet nicht, wer eine Funktion zufällig ungerufen findet.*

**Kein Eintrag in `ABSICHTLICH`.** Die Liste im Werkzeug hat zwei Einträge und einen Deckel
bei zehn — beides mit Absicht: *„Eine wachsende Liste dort ist ein Zeichen dafür, dass
weggesehen statt geprüft wird."* Achtzig Urteile gehören in ein Dokument, das man liest,
und nicht in eine Ausnahmeliste, die man vergisst.
