# Struktur der Vertiefungsarbeit

*Angelegt am 09.09.2026. Der Owner hat sie am selben Abend als eine von drei Richtungen
gewählt — bis dahin gab es 73 Dokumente, 23 Sitzungsprotokolle und keinen Plan, in welcher
Reihenfolge daraus ein Text wird.*

**Stand:** 29.09.2026 — nachgeführt über die Sitzungen 67–72. Die Bilanz in Kapitel 8 ist neu
gezählt; was sich an anderen Stellen geändert hat, steht dort als **Nachtrag 29.09.2026**. Der
alte Wortlaut bleibt stehen, damit man sieht, was vorher galt.

**Was dieses Dokument ist:** eine Landkarte vom Repo zum geschriebenen Text. Je Kapitel
steht, **was es behauptet**, **was diese Behauptung trägt** (mit Pfad), und **was ihr
fehlt**. Die dritte Spalte ist die wichtigste: Sie sagt, was beim Schreiben auffallen
würde, wenn es hier nicht stünde — und dann zu spät.

**Was es nicht ist:** eine Gliederung nach Gefühl. Jede Zeile der Spalte «trägt» zeigt auf
eine Datei, eine Messung oder eine Bildreihe, die es gibt. Wo nichts steht, steht «fehlt».

---

## Die Frage, und sie ist enger als der Titel

> **Lässt sich ein KI-erzeugtes Architekturbild gegen die Geometrie prüfen, aus der es
> entstanden ist — lokal, mit austauschbarem Modell, und so, dass eine erfundene Kubatur
> nachweislich durchfällt?**

Drei Abgrenzungen, die den Umfang festlegen:

* **Nicht** «wie erzeugt man schöne Bilder». Das Erzeugen ist eine austauschbare Stufe.
  Der Gegenstand ist das **Messen**.
* **Nicht** «wie gut ist Modell X». Die Arbeit baut ein Verfahren, keine Modellstudie.
  Welches Modell darunterliegt, entscheidet eine Registry mit Lizenzampel.
* **Nicht** «ein Werkzeug für den Bürobetrieb». Ein Prototyp mit einer Messfrage, kein
  Produkt. Was zum Produkt fehlt, gehört in den Ausblick und nicht in die Ergebnisse.

**Die ehrliche Fassung des Standes**, und sie gehört in die Einleitung und nicht in eine
Fussnote: *Die Kette ist belegt, die Aussage «geometrietreu» ist es noch nicht.* Ein Bild,
das die Geometrie-Schwelle besteht, gibt es zum Zeitpunkt dieser Struktur **nicht** — der
erste echte Lauf am Gerät (18.08.2026, Qwen-Image-Edit-2511) erreichte 0,359 und fiel
durch. Das ist ein Messwert und kein Fehlschlag, aber es ist auch keine bestandene Probe.

> **Nachtrag 29.09.2026 — der Satz gilt unverändert.** Auch sechs Wochen später hat kein Lauf
> die Schwelle bestanden; der beste Wert liegt bei 0,534 gegen 0,65 (`auf-20260923-154`).
> Dazu kommt eine Verengung: Seit dem 29.09.2026 trägt **ρ allein** das Paarurteil, denn das
> zweite Bein (Kante am Umriss) hat an echten Bildern um seine eigene Schwelle gestreut und
> ist abgeschaltet (Owner-Entscheid, Sitzung 72). Die Schwelle 0,80 von ρ ist **nicht
> geeicht**; die Messung liegt als `auf-20260929-175` beim Heimrechner.

---

## Kapitel 1 · Einleitung: die Frage und warum sie sich stellt

| | |
|---|---|
| **Behauptet** | Bildmodelle erfinden Bauteile, und niemand merkt es systematisch. Ein Prüfverfahren fehlt. |
| **Trägt** | `docs/LAGEBEURTEILUNG_2026-08-14.md` — die erste Lagebeurteilung, ausdrücklich **kein Bau**, sondern eine Bestandsaufnahme mit Lizenzangabe je Baustein. Seit dem 10.09.2026 dazu `docs/FORSCHUNGSSTAND_2026-09-10.md`: **die Prämisse ist belegt** — Aithal et al. (arXiv:2406.09358) und Sobieski et al. (arXiv:2605.05026) zeigen, dass Diffusionsmodelle Dinge erzeugen, die es nicht gab. |
| **Fehlt** | **Der Beleg trägt die Prämisse nur zur Hälfte, und die Hälfte ist präzisierbar.** Beide Arbeiten definieren Halluzination **modellintern** — Abweichung von der Trainingsverteilung oder von gelernten Strukturregeln. Ein Bild mit einem zusätzlichen Geschoss ist danach in Ordnung: Es ist ein plausibles Haus, nur nicht *dieses*. Was fehlt, ist die Häufigkeit **in dieser Anwendung**, gemessen an unserer eigenen Kette — als `auf-20260909-92` bei der HomeStation. |

---

## Kapitel 2 · Was es schon gibt, und warum es nicht genügt

| | |
|---|---|
| **Behauptet** | Die Bausteine existieren einzeln (IFC-Leser, Renderer, Bildmodelle, ControlNet); was fehlt, ist die **Verbindung mit einer Messung am Ende**. |
| **Trägt** | Werkzeugbestand: `docs/OEKOSYSTEM_2026-08-18.md`, `docs/KI_MODULE_BESTAND_2026-08-19.md`, `docs/BLENDER_ADDON_BESTAND_2026-08-18.md`, `docs/BACKBONE_2026-08-22.md`, `docs/BACKBONE_CONTROLNET_2026-08-18.md`, `docs/CONTROLNET_NAHT_2026-08-20.md`, `docs/WELCHE_APP_2026-08-19.md`. **Forschungsstand, erste Erhebung:** `docs/FORSCHUNGSSTAND_2026-09-10.md` — sechs Arbeiten, jede einzeln abgerufen und gegen ihre eigene Seite geprüft. |
| **Die Lücke, die sie benennt** | Die Literatur kennt Halluzination als Abweichung von dem, was ein Modell **gelernt** hat, und Formtreue als Vergleich zweier **Geometrien** (Chamfer, F-Score) oder zweier **Bilder** (PSNR, SSIM, LPIPS). Ein etabliertes Mass dafür, ob ein **einzelnes erzeugtes Bild** zu der **Geometrie** passt, aus der es entstand, hat diese Suche nicht gefunden. Das Nächstverwandte — GeCo (arXiv:2512.22274) — gilt für **Video** und braucht Kamerabewegung. |
| **Fehlt** | Die Erhebung ist eine Suche, keine systematische Recherche, US-beschränkt und ohne Zugriff auf CAADRIA, eCAADe, ACADIA, CAAD Futures — also gerade dort blind, wo die Frage in der Architekturinformatik verhandelt wird. *Und eine gescheiterte Suche ist ein schwacher Beleg für eine Lücke* — dieselbe Sorte Aussage, die dieses Projekt bei `tools/einbau.py` schon einmal verkleinern musste. Vor der Abgabe zu wiederholen; hier kann der Betreuer in Minuten helfen, wofür ich Stunden bräuchte. |

---

## Kapitel 3 · Die Randbedingungen sind der Entwurf

Das Kapitel, das eine reine Softwarearbeit nicht hätte. **Vier Regeln haben die Architektur
bestimmt, bevor eine Zeile geschrieben war**, und ihre Folgen sind an der Software
ablesbar.

| | |
|---|---|
| **Behauptet** | Lizenz- und Betriebsauflagen sind keine Nebenbedingung, sondern Entwurfstreiber. «Blender nur als Subprozess» erzwingt eine Prozessgrenze, die dem System auch technisch guttut. |
| **Trägt** | `CLAUDE.md` (die vier Regeln im Wortlaut), `docs/LIZENZPRUEFUNG_2026-08-18.md`, `docs/LIZENZPRUEFUNG_BINAER_2026-08-18.md`, `NOTICE`. **Ausführbar belegt**: `tools/beweis/19_regeln_ausfuehrbar.py` — Lizenzampel über die echte Registry (8 Modelle, 2 gesperrt, `waehle()` gibt FLUX-dev nicht heraus), Prozessgrenze als gemessene Abwesenheit von `ifcopenshell` und `bpy` im Produkt-venv, Wächterlauf über 540 Dateien mit 0 Treffern, Importprüfung über 165 Module. |
| **Fehlt** | Nichts Wesentliches. Dies ist das am besten belegte Kapitel — und, weil die Belege **ausführbar** sind, auch das am leichtesten zu aktualisierende. |
| **Nachtrag 29.09.2026: Regel 1 hat jetzt benannte Ausnahmen, und das Kapitel muss sie zeigen** | Seit dem 22.09.2026 dürfen zwei Modelle mit Auflagen-Lizenz (`sdxl-juggernaut`, `sd35-large`) nur **messen**, nie ins Produkt; Schriften unter der Open Font License sind zugelassen. Seit dem 29.09.2026 gibt es eine **Forschungs-Ausnahme**: Qwen-Image-2.1 (Forschungslizenz, «research or evaluation purposes only») darf für die Arbeit rechnen — nur am Heimrechner und nur mit dem Schalter `AIIMAGING_FORSCHUNGSMODELLE=1`, nie Vorgabe, nie von KosmoOrbit bestellbar, jeder Lauf als «nur Forschung» markiert, vor einem Verkauf zu entfernen oder zu lizenzieren (`CLAUDE.md`, `NOTICE`, `tests/test_forschung_ausnahme.py`). **Ehrlich zur Reihenfolge:** Am selben Tag hatte ich zuerst «nicht verwenden» empfohlen, weil ein Schalter mit dem Produkt ausgeliefert würde; der Owner hat mit Blick auf den fernen Verkauf anders entschieden. Die Register-Zahlen oben (8 Modelle, 2 gesperrt) sind der Stand des Beweisskripts; das Register führt heute **9 Einträge**: 4 zulässig, davon einer **stillgelegt** (`qwen-image-2512`, 29.09.), und 5 nicht fürs Produkt (zwei FLUX-Modelle mit Non-Commercial-Lizenz, zwei «nur messen», eines unter der Forschungs-Ausnahme). *Für den Text heisst das:* Die Randbedingungen haben nicht nachgegeben, sie sind **präzisiert** worden — jede Ausnahme steht mit Datum und Auflagen im Repo und wird im Code gehalten, nicht nur im Text. Das ist ein stärkerer Beleg als eine Regel ohne Ausnahme, aber nur, wenn das Kapitel ihn so erzählt. |

---

## Kapitel 4 · Die Kette: vier Knoten und ein Graph

| | |
|---|---|
| **Behauptet** | Die Verarbeitung ist ein gerichteter Graph aus vier Knoten (`geometrie`, `multipass`, `render`, `qa`) mit Zwischenspeicher; eine Prompt-Änderung rechnet die Geometriestufen nicht neu. |
| **Trägt** | `src/aiimaging/kette.py`, `graph.py`, `seams.py`. **Als Bild**: `tools/beweis/01`–`05` — je Knoten eine Reihe, und `05_der_graph` zeigt vier Läufe, in denen die Aufrufzahl je Knoten gemessen wird (Lauf 2 ändert nur den Prompt: zwei Knoten aus dem Speicher; Lauf 4 ändert die Geometrie: alles dahinter fällt). Die ganze Kette in einem Bild: `tools/beweis/20`. |
| **Fehlt** | **Der Graph läuft nicht am Produktivweg** — `abholer.py` fährt die Stufen als gerade Abfolge, und `kette.baue_kette` hat ausserhalb seiner Tests keinen Aufrufer. **Nachtrag 10.09.2026, gemessen:** Der *Nutzen* fehlt dort trotzdem nicht. `tools/beweis/23_speicher_am_produktivweg.py` stellt Beweis 05 dieselbe Frage an `abholer.verarbeiter` und zählt die echten Blender-Aufrufe: Lauf 1 rechnet (2,48 s), eine reine Prompt-Änderung kommt aus dem Speicher (0,26 s, **kein Blender**), eine Geometrie-Änderung rechnet wieder (2,43 s). *Damit trennt sich «gebaut, aber nicht im Betrieb» von «der Nutzen fehlt» — und nur das Erste stimmt.* Im Text ist der Posten so zu formulieren, sonst behauptet er mehr, als offen ist. |

---

## Kapitel 5 · Die Kamera: was die Software selbst entscheidet

Das Kapitel mit der stärksten Bildlage und dem meisten architektonischen Gehalt.

| | |
|---|---|
| **Behauptet** | Aus einer Hüllbox lassen sich brauchbare Standpunkte **rechnen**: zwölf Richtungen, Rahmung nach Deckungsgrad, Shift statt Kippen, eine Auswahl, die mit drei statt zwölf Läufen alle Fassaden abdeckt — und innen zwei Blickarten, zwischen denen die Software bewusst **nicht** entscheidet. |
| **Trägt** | `src/aiimaging/kameras.py`, `komposition.py`, `raumkamera.py`, `glbbox.py`. Dokumente: `docs/KAMERAREGELN_2026-08-21.md`, `docs/KAMERANEIGUNG_2026-08-22.md`, `docs/STANDPUNKTE_2026-09-01.md`, `docs/RICHTUNGEN_2026-08-28.md`, `docs/BODENANTEIL_2026-08-26.md`, `docs/INNENANSICHT_2026-09-09.md`. **Als Bild**: `tools/beweis/09`–`14`, `21`, `22`. |
| **Zahlen, die im Text stehen sollten** | Zwölf Standpunkte, **8 von 8 Ecken im Bild** bei jedem, Füllgrad 0,70. Shift gegen Kippen: Lotabweichung 0,283–0,384° gegen **0,000°**, und über Gebäudehöhen von 3 bis 100 m bleibt der nötige Shift unter 2 mm — **0 von 96 Fällen** über der Objektivgrenze von 12 mm. Auswahl: 56 Kombinationen, **4 von 4 Fassaden** mit drei Kameras. Bauwerksbox: der bestellte Deckungsgrad 0,70 wird nach der Szenenbox eingehalten — **vom Gelände**; das Bauwerk schrumpft auf 0,2795. `komposition.bildanteile` gegen den gerenderten Bildinhalt: Abweichung **0,001**. |
| **Fehlt** | Die **Ableitung** der Innenstandpunkte erreicht den Produktivweg nicht — nicht wegen einer fehlenden Zeile, sondern weil der Renderweg eine glb bekommt und Räume `IfcSpace` sind. Die Zuständigkeit ist als `auf-20260909-91` an den Cloud-Worker gestellt; **die Antwort fehlt und gehört ins Kapitel, nicht in den Ausblick.** |
| **Nachtrag 29.09.2026** | **Die Antwort auf `auf-91` ist da** (21.09.2026, übertragen am 22.09.): Die Ableitung liegt bei KosmoOrbit und ist dort seit dem 19.09. in Betrieb; sie schickt die Standpunkte als benannte Kameras mit. Gerendert hatte drüben damals noch niemand einen Innenraum-Auftrag. Auf dem eigenen Weg ist die Lücke ebenfalls geschlossen: Die Software liest die Räume einmal beim Anlegen des Projekts, und die Innenansicht über die Mappe ist am Gerät gerechnet — Kamera im Raum, das Blender-Bild zeigt innen (`auf-20260922-141`, 23.09.2026; Einbau-Posten C18). Vorbehalte laut Antwort: ohne Prompt bricht der Lauf ab, die Rückwand ist schwarz (ungemessen), beurteilt ist nur das Blender-Bild. Bestellungen aus KosmoOrbit sind gebaut, am Gerät unbestätigt (C19). |

---

## Kapitel 6 · Das Messen: der Kern der Arbeit

| | |
|---|---|
| **Behauptet** | `score = sqrt(polarität · spearman · geom_iou)` misst Geometrie-Treue massstabsblind und fängt eine erfundene Kubatur. Zwei Anteile, weil **Existenz und Richtigkeit zwei Fragen sind**. |
| **Trägt** | `src/aiimaging/geometrie_qa.py`, `maske.py`, `tiefenschaetzer.py`, `paarschwellen.py`. Dokumente: `docs/POLARITAET_2026-08-21.md`, `docs/POLARITAET_UND_STAERKE_2026-08-22.md`, `docs/BRAUCHT_ES_GEOM_IOU_2026-08-26.md`, `docs/MASKE_2026-08-21.md`, `docs/TIEFENKANTE_2026-08-21.md`, `docs/RANDKANTE_2026-08-22.md`, `docs/EICHUNG_2026-08-23.md`, `docs/SCHWELLENSTUDIE_ECHT_2026-08-26.md`. **Als Bild**: `tools/beweis/04`, `15`, `16`, `17`. |
| **Zahlen, die den Kern tragen** | *Massstabsblindheit:* eine streng monotone Umrechnung (Potenz 2, Faktor 10, Nullpunkt −50 m — kein Meterwert stimmt mehr) ergibt weiterhin **1,000**. *Halluzination:* eine erfundene Kubatur erreicht ρ **0,966** und fällt trotzdem durch, weil `geom_iou` = **0,101**. *Wozu die Maske:* Bauwerk in der Tiefe gespiegelt, Boden stimmt — ρ über das ganze Bild **0,962**, über die Maske **−1,000**; bei 16 px Versatz 0,993 gegen −0,607. *Wozu der Nullanker:* Rauschen, Graufläche und Verlauf erreichen alle **IoU 0,6016** — die Silhouette allein trägt 60 %. |
| **Fehlt** | **Die tragende Messung am Gerät.** Alle Zahlen oben sind an synthetischen Karten oder an Soll-Karten gerechnet; der Tiefenschätzer braucht `torch`. Nach der Hausregel vom 24.08.2026 dürfen sie **ausschliessen, aber nichts zusagen**. Der Text muss diese Grenze an jeder Zahl mitführen — sonst liest er wie ein Ergebnis, das er nicht ist. |
| **Nachtrag 29.09.2026** | Drei Dinge haben sich seit dem 16.09. am Kern verschoben. **(1) Saubere Bilder sind nicht messbar:** Die Prüfung hält den Boden, den das Bildmodell vor das Haus malt, für einen Fehler und nennt gerade die besten Bilder «nicht messbar» (Sitzung 71 §17). **(2) Ein Kandidat dafür ist gefallen:** Die Ordnung an Tiefensprüngen, am 24.09. gebaut, gab am Heimrechner einer grauen Fläche die Bestnote und stellte das einzige Nein-Bild über alle Ja-Bilder (`auf-172`) — wieder herausgenommen, bevor sie etwas entschied. Nächster Kandidat ist der Umriss aus den Bildkanten; nicht angefangen. **(3) Das Paarurteil hängt an ρ allein** (siehe oben), mit ungeeichter Schwelle. *Für den Text:* Der Satz «fängt eine erfundene Kubatur» bleibt belegt; der Satz «lässt ein gutes Bild durch» ist es nicht. |

---

## Kapitel 7 · Die Methode: wie in dieser Arbeit entschieden wurde

**Das Kapitel, das die Arbeit von einem Softwareprojekt unterscheidet.** Es ist bereits
geschrieben, nur verstreut: in 23 Sitzungsprotokollen und im Lexikon.

| | |
|---|---|
| **Behauptet** | Ein Prototyp, der über Wochen und über fremde Wartende hinweg entsteht, braucht Regeln über den Umgang mit dem eigenen Nichtwissen. Vier davon sind hier entstanden und haben nachweislich Entscheidungen verändert. |
| **Trägt** | `docs/LEXIKON.md` (die Begriffe mit ihrer Herkunft), `docs/sitzungen/` (23 Protokolle mit Begründung), `docs/ENTSCHEIDUNGEN_2026-09-02.md`. |
| **Die vier Regeln** | **Die dritte Antwort** — nicht messbar ist weder bestanden noch durchgefallen. **Die Mutationsprobe** — ein Wächter, der nicht fällt, bewacht nichts. **Vorprüfung gegen tragende Messung** — Renders und Nullanker können ein Mass widerlegen, nie tragen; drei Vorschläge sind daran gefallen. **Eine Zahl gehört an die Bedingung, unter der sie gemessen wurde.** |
| **Die Auswahl ist getroffen** | `docs/METHODE_2026-09-10.md` — je Regel drei bis fünf Fälle, jeder datiert, jeder mit der Zahl, die ohne die Regel dagestanden hätte. Auswahlkriterium: Der Fall muss eine Entscheidung **gedreht** haben, und es muss benennbar sein, was sonst geschehen wäre. |
| **Der Befund beim Zusammentragen** | **Es gibt eine fünfte Regel, und sie erklärt mehr Fälle als die vier anderen.** *Ein Fehlschlag, der wie ein Erfolg aussieht, wird nicht gefunden — er wird geglaubt.* Sechs Vorkommen in vier Wochen und vier Modulen: der liegengebliebene Report (Sitzung 03, bbox −4…7,85 statt 0…8), die Dateigrösse als Beleg (Sitzung 05, 75 920 Bytes für 0 von 147 456 hellen Bildpunkten), der ins Leere laufende Sonnenstand (26.08.), «abgelegt ist nicht ausgeliefert» (03.09. und wieder 10.09.), der Nachbau, der in einem von zwei Fällen exakt traf (09.09.). Daraus folgt eine Bauregel: **Jede Erfolgsmeldung muss an etwas hängen, das unabhängig vom Erzähler ist.** |
| **Vier neue Fälle, 09.–12.09.2026** | Alle vier tragen dieselbe Form und stützen die fünfte Regel: **(1)** Ein Zähler, der Aufträge *ohne* Antwort zählt, meldet nie einen Posten, dessen Antwort längst da ist — 21 von 23 standen so. **(2)** Ein Wächter, der die Diensteinheit als *Datei* vergleicht, sieht die örtliche Ergänzung daneben nicht: Die Datei deckte sich, der Dienst lief anders. **(3)** Ein Zeuge, der nur Wörterbuch**einträge** kennt, verneint die Frage «ist das deutsch?» für ein Wort, das die **Regeln** übersetzen könnten — und die Übersetzung läuft gar nicht erst an. **(4)** Eine Kennzahl, die für eine leere Wand und für einen strukturierten Raum **dieselbe Zahl** liefert. |
| **Der gemeinsame Nenner, und er ist schärfer als die fünfte Regel** | *Ein Wächter, der nur kennt, was man ihm genannt hat, fängt keine Neuigkeit.* Alle vier Fälle sind derselbe Bauplan: Die Prüfung ist gegen eine **Liste** gebaut statt gegen die **Wirklichkeit**. Die Regel dazu kam von der HomeStation aus deren Renderprojekt: **«Ein Riegel prüft, ob jedes Element der Wirklichkeit in seiner Liste steht — nicht, ob jedes Element seiner Liste in der Wirklichkeit vorkommt. Der zweite besteht immer.»** |
| **Ein Fall, in dem eine Regel etwas gekostet hat** | Am 11.09.2026 bot die HomeStation die Ebenen ihres Renderprojekts an — 121 MB, darunter genau der Tiefenanker mit Wertebereich, der dieser Arbeit fehlt. **Abgelehnt**, weil es Renders aus einem laufenden Wettbewerbsprojekt sind und dieses Repo öffentlich ist. *Die Stelle, an der eine Regel etwas kostet, ist die, an der sie gilt* — für Kapitel 3 der beste verfügbare Beleg, dass die Randbedingungen nicht nachträglich zurechtgelegt wurden. |
| **Nachtrag 29.09.2026: drei weitere Fälle derselben Form** | **(1) Die Zwillingserkennung war tot** (24.09.): Die Proben fütterten die Tiefenkarte in Zeilen, der Betrieb liefert sie flach; die Erkennung gab still «nicht vergleichbar» zurück und hat im Betrieb nie gegriffen. *Eine Probe, die die Datenform selbst erfindet, prüft die Erfindung.* **(2) Glas zählte nicht als durchsichtig** (29.09.): Unsere Prüfung kannte nur einen Weg, Durchsichtigkeit anzugeben (`alphaMode: BLEND`); Glas «deckend mit Durchlass», wie KosmoOrbit es ausgeben will, wäre als «keine durchsichtigen Materialien» gemeldet worden. Gefunden, weil **sie** es als Bedingung gestellt haben — genau der gemeinsame Nenner oben: eine Prüfung gegen eine Liste statt gegen die Wirklichkeit. **(3) «Abgelegt ist nicht ausgeliefert», zum dritten Mal** (24.–29.09.): Unsere Antwort auf B161 und sechs Aufträge lagen fünf Tage nur in unserem Repo, während drüben «offen, noch keine Antwort» stand. |
| **Fehlt** | Nur noch die Kürzung fürs Schreiben: je Regel **einen** Fall ausführen, die übrigen nennen. Inzwischen sind es dreizehn ausgeführte Fälle — als Aufzählung ginge jede Regel darin unter. |

---

## Kapitel 8 · Der Einbau: Software, die anderswo laufen soll

| | |
|---|---|
| **Behauptet** | Gebauter Code ist kein Ergebnis, sondern eine Zwischenstufe; das Ergebnis ist Code, der in KosmoOrbit läuft. Dazwischen liegen drei fremde Wartende, und der Rückstand muss **gezählt** werden, nicht geschätzt. |
| **Trägt** | `src/aiimaging/einbau.py`, `auftrag.py`, `auftragspost.py`, `tools/einbau.py`; `docs/EINBAU_STAND.md`, `docs/EINBAU_CLOUDWORKER_2026-08-22.md`, `auftraege/` mit 90+ Aufträgen und ihren Ergebnissen (**Nachtrag 29.09.2026:** Laufnummer inzwischen 178). **Als Bild**: `tools/beweis/06`–`08` (MCP-Fähigkeiten, Freigabe mit Token, Torwächter). |
| **Der Zustand, der einen eigenen Namen bekam** | *gebaut, am Gerät unbestätigt* — weder erledigt noch offen. Die dritte Antwort, angewandt auf den Einbau. |
| **Der zweite Zustand, der einen Namen bekam** | *verworfen* — entschieden, dass etwas **nicht** gebaut wird. Bis zum 11.09.2026 hiess das genauso wie *entschieden, nicht gebaut*, und ein abgelehnter Posten stand darum für immer im Rückstand, an etwas, das niemand je bauen wird. |
| **Die Bilanz, Stand 16.09.2026** (bleibt als Vergleich stehen) | **8 von 35 Posten sind nicht in der Software** — am 09.09. waren es 22 von 34. Fünfzehn Posten sind in einer Woche geschlossen worden, **und nur einer davon durch neuen Code.** Alle anderen lagen fertig da und waren nie nachgetragen: Die Bestätigung stand seit Tagen in einer Antwort, die niemand gelesen hatte. |
| **Und die Zahl, die dagegen steht** | **Der Rückstand bei den Wartenden ist im selben Zeitraum von 14 auf 18 Aufträge gewachsen, der älteste von 16 auf 25 Tage. Seit dem 08.09.2026 — acht Tagen — hat keiner der drei Worker geantwortet.** Von den 18 liegen 10 bei `local` (über meiner eigenen Selbstbindung von 8), 7 bei `cloud`, 1 bei `ui`. |
| **Was das für das Kapitel bedeutet** | Die beiden Zahlen zusammen sind das Ergebnis, nicht die erste allein. *Der eigene Rückstand liess sich durch Lesen halbieren; der fremde nicht durch Schreiben.* Ein Verteilmodell über drei fremde Wartende hat eine Untergrenze, die nicht in der eigenen Sorgfalt liegt — und sie zu benennen ist ehrlicher, als sie als Organisationsproblem wegzuerklären. |
| **Fehlt** | Der Grund für die acht stillen Tage. Er ist **nicht gemessen**: Ob drüben niemand gearbeitet hat, ob die Aufträge nicht ankamen, oder ob sie ankamen und liegen blieben, unterscheidet dieses Repo nicht. *Genau die Unterscheidung, die `auftragspost.py` für den Hinweg gebaut hat — für den Rückweg fehlt sie.* |
| **Die Bilanz, Stand 29.09.2026 — und wie gezählt wurde** | **23 von 60 Posten sind nicht in der Software.** Gezählt zweimal, unabhängig: `python tools/einbau.py` meldet «EINBAU-STAND: 23 von 60 Posten noch nicht in der Software»; die Zustandsspalte der 60 Tabellenzeilen in `docs/EINBAU_STAND.md` von Hand ausgezählt ergibt dasselbe — **33 erledigt, 4 verworfen, 16 gebaut, am Gerät unbestätigt, 4 halb, 3 offen.** Am 16.09. waren es 8 von 35. **Der Anteil ist also gestiegen, von knapp einem Viertel auf gut ein Drittel.** Der Grund ist nachgezählt (Tabelle vom 16.09., Commit `cfc701e`, gegen die heutige): **25 Posten sind neu dazugekommen**, und 16 der 23 offenen stammen daraus — 13 davon *gebaut, am Gerät unbestätigt* (iPad-App und ihre Schriften, Ebenen, Glas, Vorgabemodell, Modellangabe im Ergebnis, Tor-Block in ihren Wörtern, Forschungs-Ausnahme u. a.), 2 halb, 1 offen (das Urteil am Render-Knoten, B9). **Von den 35 alten Posten sind heute 7 nicht in der Software, am 16.09. waren es 8.** Der alte Bestand ist also kaum vorangekommen; der neue ist fast ganz auf dem Stand «hier fertig, dort nie gesehen». Insgesamt stehen 16 der 23 auf *gebaut, am Gerät unbestätigt*; nur 3 sind wirklich offen. |
| **Der Rückstand bei den Wartenden, 29.09.2026** | **6 Aufträge ohne Antwort, alle bei `local`, der älteste 5 Tage** (`auf-20260924-173`). Bei `cloud` und `ui`: **null.** Am 16.09. waren es 18, der älteste 25 Tage. **Die Zahl ist nicht durch Warten gesunken, sondern durch Zustellen:** Die sechs Cloud-Aufträge lagen bis zum 29.09. nur in unserem Repo; `tools/einbau.py` meldete drei davon als «NICHT AUSGELIEFERT». Auf Owner-Entscheid «b» sind sie direkt in den Eingangsordner von KosmoOrbit gelegt worden — und **am selben Tag beantwortet** (E123, E124 und vier weitere). Daneben meldet dasselbe Werkzeug zwei Listen, die bei **uns** liegen: **12 Antworten, deren Kennung in keinem Dokument unter `docs/` steht**, und 7 Einbau-Posten, deren Aufträge alle beantwortet sind — bei den meisten ist die Antwort am 29.09. gelesen und vermerkt, schliesst den Posten aber nicht. *Der Leserückstand vom 16.09. ist in kleinerer Form wieder da; er wächst, sobald man nicht hinsieht.* |
| **Was die neue Zahl für das Kapitel bedeutet** | **Berichtigt am Satz oben:** «Der fremde Rückstand liess sich nicht durch Schreiben halbieren» war für den Zeitraum 24.–29.09. falsch gelesen. Er lag nicht drüben, sondern bei uns: *Ein Block, der im eigenen Repo liegt, ist nicht zugestellt.* Das KosmoOrbit-Repo sagt es selbst: «Ein Auftrag, den sein Adressat nicht erreichen kann, ist kein Rückstand bei ihm — er ist einer beim Absender.» **Was stehen bleibt:** Ob die acht stillen Tage vom 08.–16.09. denselben Grund hatten, ist nicht gemessen und darf nicht rückwirkend so erzählt werden. **Und was die Zählung nicht zeigt:** KosmoOrbit hat v0.1.5 am 25.09.2026 **ohne** das erste echte Bild vom Heimrechner geschnitten (verschoben nach v0.1.6); das Urteil am Render-Knoten (KV7) fehlt darin. Eine beantwortete Frage ist kein eingebauter Posten — genau der Unterschied, um den es in diesem Kapitel geht. |

---

## Kapitel 9 · Diskussion: was gezeigt ist und was nicht

Der Text steht und fällt mit diesem Kapitel. **Drei Trennungen sind sauber zu ziehen:**

1. **Belegt und am Gerät bestätigt** — IFC → glb an 40 echten Dateien; der Multipass auf
   Blender 4.2 und 5.2; ein echter Render mit echten Gewichten (18.08.); die
   MCP-Registrierung (18.08.).
2. **Belegt, aber nur hier** — die ganze Geometrieseite: Kamerasetzung, Rahmung, Hüllboxen,
   Innenraum. 21 Beweisskripte, 193 Bilder, seriell gefahren und reproduzierbar.
3. **Gebaut und ungeprüft** — die Geometrie-Treue-Zahl mit echtem Schätzer über eine echte
   Kette; das Stil-Gate und seine Schwelle; das LoRA-Training (Naht gebaut, **nie ein
   Training ausgeführt**).

> **Nachtrag 29.09.2026 zu den drei Trennungen:** In die **erste** gehören seither: das erste
> Bild über die Knotenansicht (`auf-164`, 24.09.), alle drei automatischen Kameras am Testbau
> (`auf-169`), die Innenansicht über die Mappe (`auf-141`), der Speicher-Riegel je Modell
> (`auf-170`). In die **dritte** kommen dazu: die iPad-App (übersetzt auf einem Mac, auf
> einem iPad nie gelaufen), die Ebenen nach E124 (mit echtem Blender erzeugt, KI-Bild und
> Prüfung darin Attrappen; der ganz echte Lauf ist `auf-176`) und der Forschungsweg mit
> Qwen-Image-2.1 (`auf-178`).

**Und der eine Satz, der nicht fehlen darf:** Ein Bild, das die Geometrie-Schwelle
besteht, gibt es noch nicht. Die Arbeit zeigt ein Verfahren, das eine erfundene Kubatur
durchfallen lässt — sie zeigt nicht, dass ein echtes Bild sie besteht.

---

## Kapitel 10 · Ausblick

Nur was aus der Arbeit selbst folgt, nicht was man sich wünschen könnte:

* **Die eine fehlende Messung**: ein Bild mit einem Prompt ohne Bauteile und einer
  Geometrie, die ein Gebäude ist statt einer offenen Schachtel — die Schwelle einmal
  bestanden. Alles andere ist danach anders zu bewerten.
* **Den Graphen an den Produktivweg bringen** (Kapitel 4).
* **Die Zuständigkeit für die Innenstandpunkte klären** (Kapitel 5, `auf-91`).
* **Das Stil-Gate eichen** — die Schwelle ist gebaut und ungeprüft, und eine ungeprüfte
  Schwelle ist eine Meinung mit Nachkommastellen.
* **Nachtrag 29.09.2026:** **Die Schwelle von ρ eichen** (`auf-175`) — sie trägt das
  Paarurteil jetzt allein. **Eine Prüfung für saubere Bilder** finden (Kapitel 6, Nachtrag).
  Und der Punkt «Innenstandpunkte» ist zur Hälfte erledigt: Auf dem eigenen Weg ist die
  Innenansicht über die Mappe lieferbar und am Gerät belegt (`auf-141`, 23.09.); Bestellungen
  aus KosmoOrbit sind gebaut, am Gerät unbestätigt (Einbau-Posten C19).

---

## Anhänge

| | |
|---|---|
| **A · Lexikon** | `docs/LEXIKON.md`. **Kein Nebenprodukt, sondern Anhang der Arbeit** (CLAUDE.md): jeder nicht-architektonische Fachbegriff für Leser:innen ohne Informatikhintergrund, keine Definition, die einen anderen unerklärten Begriff voraussetzt. |
| **B · Wie man eine Software von Grund auf baut** | `docs/SOFTWARE_VON_GRUND_AUF.md`. **Owner-Entscheid 22.09.2026:** die Grundkonzepte, nach denen Visbox gebaut ist, für Leser:innen, die über den Bau einer Software entscheiden, ohne selbst zu programmieren — erklärt an diesem Projekt, nur Text, mit Verweisen in Anhang A. Unterlage, nicht Text der Arbeit. Nachgeführt am 29.09.2026. |
| **C · Beweisbilder** | 21 Skripte unter `tools/beweis/` (**Nachtrag 29.09.2026:** heute 31 Skripte; die Bildzahl unten ist seither nicht neu gefahren), seriell gefahren von `tools/beweise_fahren.py`, **193 Bilder**. Jedes Bild trägt seine Messwerte im Dateinamen — *eine Zahl gehört an die Bedingung, unter der sie gemessen wurde.* Für den Druck ist eine Auswahl zu treffen; die Reihe selbst ist reproduzierbar und gehört als Verweis in den Text. |
| **D · Messreihen** | Die datierten Studien in `docs/` (Schwellen, Rauschboden, Empfindlichkeit, Seedauswahl, Deckelstudie, Innenansicht). |
| **E · Sitzungsprotokolle** | `docs/sitzungen/`, 23 Stück. **Nachtrag 29.09.2026: 72 Stück.** Nicht zum Abdruck, aber als Beleg für Kapitel 7. |
| **F · Aufträge und Antworten** | `auftraege/`. Der Beleg für Kapitel 8 — und das einzige Material, das zeigt, wie die Zusammenarbeit mit den drei Wartenden tatsächlich lief. |

---

## Was beim Schreiben zuerst zu tun ist

In dieser Reihenfolge, und die Reihenfolge ist begründet:

1. **Die Prämisse messen, nicht nur belegen** (Kapitel 1). Belegt ist sie seit dem
   10.09.2026 aus der Literatur — aber modellintern, und damit nicht ganz für unsere
   Frage. Die Häufigkeit in dieser Anwendung liefert `auf-20260909-92`.
2. **Den Forschungsstand über die Bauinformatik nachziehen** (Kapitel 2). Die erste
   Erhebung steht; sie ist an genau der Stelle blind, an der die Frage vermutlich schon
   gestellt wurde.
3. **Kapitel 3, 5, 7 schreiben.** Sie sind belegt, sie sind bebildert, und sie stehen
   nicht unter Vorbehalt.
4. **Kapitel 6 mit dem Vorbehalt an jeder Zahl schreiben.** Wer ihn erst am Schluss
   nachträgt, schreibt zweimal.
5. **Kapitel 9 zuletzt.** Es kann sich noch ändern — wenn die Schwelle einmal bestanden
   wird, ändert sich der ganze Ton der Arbeit.
