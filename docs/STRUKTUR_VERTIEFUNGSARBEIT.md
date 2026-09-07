# Struktur der Vertiefungsarbeit

*Angelegt am 09.09.2026. Der Owner hat sie am selben Abend als eine von drei Richtungen
gewählt — bis dahin gab es 73 Dokumente, 23 Sitzungsprotokolle und keinen Plan, in welcher
Reihenfolge daraus ein Text wird.*

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

---

## Kapitel 1 · Einleitung: die Frage und warum sie sich stellt

| | |
|---|---|
| **Behauptet** | Bildmodelle erfinden Bauteile, und niemand merkt es systematisch. Ein Prüfverfahren fehlt. |
| **Trägt** | `docs/LAGEBEURTEILUNG_2026-08-14.md` — die erste Lagebeurteilung, ausdrücklich **kein Bau**, sondern eine Bestandsaufnahme mit Lizenzangabe je Baustein. |
| **Fehlt** | Der Beleg für die Prämisse selbst: *dass* Bildmodelle in dieser Anwendung Geschosse hinzuerfinden, ist im Repo behauptet und nicht gemessen. Entweder eine Literaturstelle oder eine eigene kleine Messreihe am Gerät. **Das ist die einzige echte Lücke in Kapitel 1, und sie steht am Anfang des Textes.** |

---

## Kapitel 2 · Was es schon gibt, und warum es nicht genügt

| | |
|---|---|
| **Behauptet** | Die Bausteine existieren einzeln (IFC-Leser, Renderer, Bildmodelle, ControlNet); was fehlt, ist die **Verbindung mit einer Messung am Ende**. |
| **Trägt** | `docs/OEKOSYSTEM_2026-08-18.md`, `docs/KI_MODULE_BESTAND_2026-08-19.md`, `docs/BLENDER_ADDON_BESTAND_2026-08-18.md`, `docs/BACKBONE_2026-08-22.md`, `docs/BACKBONE_CONTROLNET_2026-08-18.md`, `docs/CONTROLNET_NAHT_2026-08-20.md`, `docs/WELCHE_APP_2026-08-19.md` |
| **Fehlt** | Eine Einordnung gegenüber **veröffentlichter** Arbeit. Der Bestand ist als Werkzeugbestand erhoben, nicht als Forschungsstand. Für eine Vertiefungsarbeit an der ETH ist das zu wenig — hier fehlt Literatur, nicht Code. |

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

---

## Kapitel 4 · Die Kette: vier Knoten und ein Graph

| | |
|---|---|
| **Behauptet** | Die Verarbeitung ist ein gerichteter Graph aus vier Knoten (`geometrie`, `multipass`, `render`, `qa`) mit Zwischenspeicher; eine Prompt-Änderung rechnet die Geometriestufen nicht neu. |
| **Trägt** | `src/aiimaging/kette.py`, `graph.py`, `seams.py`. **Als Bild**: `tools/beweis/01`–`05` — je Knoten eine Reihe, und `05_der_graph` zeigt vier Läufe, in denen die Aufrufzahl je Knoten gemessen wird (Lauf 2 ändert nur den Prompt: zwei Knoten aus dem Speicher; Lauf 4 ändert die Geometrie: alles dahinter fällt). Die ganze Kette in einem Bild: `tools/beweis/20`. |
| **Fehlt** | **Der Graph läuft nicht am Produktivweg.** `abholer.py` fährt die Stufen als gerade Abfolge; `kette.baue_kette` hat ausserhalb seiner Tests keinen Aufrufer. Das ist im Text zu sagen und nicht zu verschweigen — es ist der Unterschied zwischen «gebaut» und «im Betrieb». |

---

## Kapitel 5 · Die Kamera: was die Software selbst entscheidet

Das Kapitel mit der stärksten Bildlage und dem meisten architektonischen Gehalt.

| | |
|---|---|
| **Behauptet** | Aus einer Hüllbox lassen sich brauchbare Standpunkte **rechnen**: zwölf Richtungen, Rahmung nach Deckungsgrad, Shift statt Kippen, eine Auswahl, die mit drei statt zwölf Läufen alle Fassaden abdeckt — und innen zwei Blickarten, zwischen denen die Software bewusst **nicht** entscheidet. |
| **Trägt** | `src/aiimaging/kameras.py`, `komposition.py`, `raumkamera.py`, `glbbox.py`. Dokumente: `docs/KAMERAREGELN_2026-08-21.md`, `docs/KAMERANEIGUNG_2026-08-22.md`, `docs/STANDPUNKTE_2026-09-01.md`, `docs/RICHTUNGEN_2026-08-28.md`, `docs/BODENANTEIL_2026-08-26.md`, `docs/INNENANSICHT_2026-09-09.md`. **Als Bild**: `tools/beweis/09`–`14`, `21`, `22`. |
| **Zahlen, die im Text stehen sollten** | Zwölf Standpunkte, **8 von 8 Ecken im Bild** bei jedem, Füllgrad 0,70. Shift gegen Kippen: Lotabweichung 0,283–0,384° gegen **0,000°**, und über Gebäudehöhen von 3 bis 100 m bleibt der nötige Shift unter 2 mm — **0 von 96 Fällen** über der Objektivgrenze von 12 mm. Auswahl: 56 Kombinationen, **4 von 4 Fassaden** mit drei Kameras. Bauwerksbox: der bestellte Deckungsgrad 0,70 wird nach der Szenenbox eingehalten — **vom Gelände**; das Bauwerk schrumpft auf 0,2795. `komposition.bildanteile` gegen den gerenderten Bildinhalt: Abweichung **0,001**. |
| **Fehlt** | Die **Ableitung** der Innenstandpunkte erreicht den Produktivweg nicht — nicht wegen einer fehlenden Zeile, sondern weil der Renderweg eine glb bekommt und Räume `IfcSpace` sind. Die Zuständigkeit ist als `auf-20260909-91` an den Cloud-Worker gestellt; **die Antwort fehlt und gehört ins Kapitel, nicht in den Ausblick.** |

---

## Kapitel 6 · Das Messen: der Kern der Arbeit

| | |
|---|---|
| **Behauptet** | `score = sqrt(polarität · spearman · geom_iou)` misst Geometrie-Treue massstabsblind und fängt eine erfundene Kubatur. Zwei Anteile, weil **Existenz und Richtigkeit zwei Fragen sind**. |
| **Trägt** | `src/aiimaging/geometrie_qa.py`, `maske.py`, `tiefenschaetzer.py`, `paarschwellen.py`. Dokumente: `docs/POLARITAET_2026-08-21.md`, `docs/POLARITAET_UND_STAERKE_2026-08-22.md`, `docs/BRAUCHT_ES_GEOM_IOU_2026-08-26.md`, `docs/MASKE_2026-08-21.md`, `docs/TIEFENKANTE_2026-08-21.md`, `docs/RANDKANTE_2026-08-22.md`, `docs/EICHUNG_2026-08-23.md`, `docs/SCHWELLENSTUDIE_ECHT_2026-08-26.md`. **Als Bild**: `tools/beweis/04`, `15`, `16`, `17`. |
| **Zahlen, die den Kern tragen** | *Massstabsblindheit:* eine streng monotone Umrechnung (Potenz 2, Faktor 10, Nullpunkt −50 m — kein Meterwert stimmt mehr) ergibt weiterhin **1,000**. *Halluzination:* eine erfundene Kubatur erreicht ρ **0,966** und fällt trotzdem durch, weil `geom_iou` = **0,101**. *Wozu die Maske:* Bauwerk in der Tiefe gespiegelt, Boden stimmt — ρ über das ganze Bild **0,962**, über die Maske **−1,000**; bei 16 px Versatz 0,993 gegen −0,607. *Wozu der Nullanker:* Rauschen, Graufläche und Verlauf erreichen alle **IoU 0,6016** — die Silhouette allein trägt 60 %. |
| **Fehlt** | **Die tragende Messung am Gerät.** Alle Zahlen oben sind an synthetischen Karten oder an Soll-Karten gerechnet; der Tiefenschätzer braucht `torch`. Nach der Hausregel vom 24.08.2026 dürfen sie **ausschliessen, aber nichts zusagen**. Der Text muss diese Grenze an jeder Zahl mitführen — sonst liest er wie ein Ergebnis, das er nicht ist. |

---

## Kapitel 7 · Die Methode: wie in dieser Arbeit entschieden wurde

**Das Kapitel, das die Arbeit von einem Softwareprojekt unterscheidet.** Es ist bereits
geschrieben, nur verstreut: in 23 Sitzungsprotokollen und im Lexikon.

| | |
|---|---|
| **Behauptet** | Ein Prototyp, der über Wochen und über fremde Wartende hinweg entsteht, braucht Regeln über den Umgang mit dem eigenen Nichtwissen. Vier davon sind hier entstanden und haben nachweislich Entscheidungen verändert. |
| **Trägt** | `docs/LEXIKON.md` (die Begriffe mit ihrer Herkunft), `docs/sitzungen/` (23 Protokolle mit Begründung), `docs/ENTSCHEIDUNGEN_2026-09-02.md`. |
| **Die vier Regeln** | **Die dritte Antwort** — nicht messbar ist weder bestanden noch durchgefallen. **Die Mutationsprobe** — ein Wächter, der nicht fällt, bewacht nichts. **Vorprüfung gegen tragende Messung** — Renders und Nullanker können ein Mass widerlegen, nie tragen; drei Vorschläge sind daran gefallen. **Eine Zahl gehört an die Bedingung, unter der sie gemessen wurde.** |
| **Fehlt** | Nichts zum Belegen — aber die **Auswahl**. 23 Protokolle sind zu viel für ein Kapitel; es braucht drei bis fünf Fälle, an denen eine Regel eine Entscheidung wirklich gedreht hat. Kandidaten: der liegengebliebene Blender-Report (Sitzung 03), die Dateigrösse als vermeintlicher Beleg (Sitzung 05), «abgelegt ist nicht ausgeliefert» (03.09.), der Nachbau des Ebenenanteils, der in einem von zwei Fällen exakt traf (09.09.). |

---

## Kapitel 8 · Der Einbau: Software, die anderswo laufen soll

| | |
|---|---|
| **Behauptet** | Gebauter Code ist kein Ergebnis, sondern eine Zwischenstufe; das Ergebnis ist Code, der in KosmoOrbit läuft. Dazwischen liegen drei fremde Wartende, und der Rückstand muss **gezählt** werden, nicht geschätzt. |
| **Trägt** | `src/aiimaging/einbau.py`, `auftrag.py`, `auftragspost.py`, `tools/einbau.py`; `docs/EINBAU_STAND.md`, `docs/EINBAU_CLOUDWORKER_2026-08-22.md`, `auftraege/` mit 90+ Aufträgen und ihren Ergebnissen. **Als Bild**: `tools/beweis/06`–`08` (MCP-Fähigkeiten, Freigabe mit Token, Torwächter). |
| **Der Zustand, der einen eigenen Namen bekam** | *gebaut, am Gerät unbestätigt* — weder erledigt noch offen. Die dritte Antwort, angewandt auf den Einbau. |
| **Fehlt** | Eine ehrliche Bilanz: Von 34 Posten sind zum 09.09.2026 **22 nicht in der Software**, und der Rückstand bei den Wartenden liegt bei 14 Aufträgen, der älteste 16 Tage. Das gehört als Zahl in den Text — es ist das ehrlichste Ergebnis des Kapitels. |

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

---

## Anhänge

| | |
|---|---|
| **A · Lexikon** | `docs/LEXIKON.md`. **Kein Nebenprodukt, sondern Anhang der Arbeit** (CLAUDE.md): jeder nicht-architektonische Fachbegriff für Leser:innen ohne Informatikhintergrund, keine Definition, die einen anderen unerklärten Begriff voraussetzt. |
| **B · Beweisbilder** | 21 Skripte unter `tools/beweis/`, seriell gefahren von `tools/beweise_fahren.py`, **193 Bilder**. Jedes Bild trägt seine Messwerte im Dateinamen — *eine Zahl gehört an die Bedingung, unter der sie gemessen wurde.* Für den Druck ist eine Auswahl zu treffen; die Reihe selbst ist reproduzierbar und gehört als Verweis in den Text. |
| **C · Messreihen** | Die datierten Studien in `docs/` (Schwellen, Rauschboden, Empfindlichkeit, Seedauswahl, Deckelstudie, Innenansicht). |
| **D · Sitzungsprotokolle** | `docs/sitzungen/`, 23 Stück. Nicht zum Abdruck, aber als Beleg für Kapitel 7. |
| **E · Aufträge und Antworten** | `auftraege/`. Der Beleg für Kapitel 8 — und das einzige Material, das zeigt, wie die Zusammenarbeit mit den drei Wartenden tatsächlich lief. |

---

## Was beim Schreiben zuerst zu tun ist

In dieser Reihenfolge, und die Reihenfolge ist begründet:

1. **Die Prämisse belegen** (Kapitel 1). Sie steht am Anfang und ist die einzige Lücke,
   die den ganzen Text trägt.
2. **Den Forschungsstand nachziehen** (Kapitel 2). Literatur, nicht Code — und der
   einzige Punkt, an dem diese Arbeit als ETH-Arbeit heute zu dünn ist.
3. **Kapitel 3, 5, 7 schreiben.** Sie sind belegt, sie sind bebildert, und sie stehen
   nicht unter Vorbehalt.
4. **Kapitel 6 mit dem Vorbehalt an jeder Zahl schreiben.** Wer ihn erst am Schluss
   nachträgt, schreibt zweimal.
5. **Kapitel 9 zuletzt.** Es kann sich noch ändern — wenn die Schwelle einmal bestanden
   wird, ändert sich der ganze Ton der Arbeit.
