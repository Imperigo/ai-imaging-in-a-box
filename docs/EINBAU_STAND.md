# Der Weg hinein — Stand

**Wozu dieses Blatt.** `docs/COCKPIT_BESTAND_2026-08-19.md` §4 hat am 19.08.2026 den
vollständigen Weg aufgelistet, auf dem KosmoVis in KosmoOrbit erscheint: acht Posten über
das Cockpit (A1–A8), sieben über die Brücke (B1–B7). **Danach hat niemand Buch geführt.**
Sieben Tage später waren mehrere Posten still erledigt, mehrere still noch offen, und
niemand konnte sagen, welche.

Das ist dieselbe Sorte Lücke, die dieses Projekt im Code jagt — eine Aufstellung, die
stimmte, als sie geschrieben wurde. Sie steht hier darum mit **Datum und Beleg**, und
`tests/test_einbau_stand.py` hält sie: Jeder erledigte Posten nennt einen Beleg, den es
gibt; jeder offene nennt einen Auftrag.

**Seit dem 26.08.2026 gilt zusätzlich:** «Niemand» ist keine zulässige Angabe mehr. Der
Owner-Auftrag desselben Tages macht den *Einbau* zum Ziel — und ein Posten ohne
Adressaten wird nie eingebaut, ohne dass es jemandem auffällt. `tools/einbau.py` zählt
das nach und **scheitert mit Rückgabewert 1**, sobald ein offener Posten niemanden nennt.

**Erledigtes wird abgehakt, nicht gelöscht** (Hausregel).

**Legende:** 🟩 = liegt in **unserem** Repo · 🟥 = liegt in einem **fremden** Repo, dort
wird ohne Rückfrage nichts geändert.

**Und seit dem 27.08.2026 sagt jede erledigte Zeile, WORAUF ihr Beleg ruht** — eine von
zwei Angaben, sonst scheitert `tools/einbau.py`:

* **belegt im Repo:** Die Aussage ist im Repo entschieden. *Nicht zulässig, wenn der Beleg
  einen Kommandozeilenschalter, eine `.service`/`.timer`-Einheit oder einen Pfad nach
  `betrieb/` nennt — alle drei sagen etwas darüber, **wie** etwas aufgerufen wird, und das
  steht in der Installation und nicht in der Datei.*
* **belegt am Gerät:** Ein Auftrag, auf den drüben **geantwortet** wurde, oder die
  **Uhrzeit** einer Messung dort.

*Der Anlass ist `B8`. Es stand sechs Tage als erledigt, weil die eingecheckte
Diensteinheit den nötigen Schalter trug — die installierte stammte vom 20.08. und kannte
ihn nicht. Der alte Wächter prüfte, ob ein Beleg **existiert**, und der existierte.*

---

## Weg A — über das Cockpit (MCP-Knoten)

| # | Posten | Zustand | Seit | Beleg / treibender Auftrag |
|---|---|---|---|---|
| A1 | `mcp<2` festschreiben — der Server ist gegen die 1.x-Dekoratorschnittstelle geschrieben | 🟩 **erledigt** | 2026-08-19 | **belegt im Repo:** `pyproject.toml` (`mcp = ["mcp>=1.27,<2"]`) |
| A2 | Ausgabeschema-Bruch in `aiimaging_query_render` (`None`, wo ein String zugesagt war) | 🟩 **erledigt** | 2026-08-18 | **belegt im Repo:** `src/aiimaging/mcp_schemas.py` (`status` nullbar, mit dem Grund im Kommentar) |
| A3 | Kein `additionalProperties: false` in unseren Eingabeschemata | 🟩 **erledigt** | 2026-08-18 | **belegt im Repo:** `mcp_schemas.pruefe_vertrag` prüft es für **jeden** Vertrag, nicht einmalig von Hand |
| A4 | Klären, warum `/api/mcp/tools` keine Schemata durchreicht | 🟩 **erledigt** | 2026-09-10 | **belegt am Gerät:** `auf-20260826-58`, beendet **06.09.2026 um 19:38:52**, am laufenden Backend gemessen: Login HTTP 200, `GET /api/mcp/tools` HTTP 200, **282 Werkzeuge, davon 4 von `aiimaging` — alle vier mit vollem `input_schema` UND `output_schema`**, gegengeprüft direkt per stdio am MCP-Server (4/4 ebenso). **Die Ursache ist gefunden und war nicht bei uns:** Die MCP-SDK-Fassung 2.x benannte `inputSchema`/`outputSchema` in `input_schema`/`output_schema` um; `_tool_schema` im fremden Backend fragte nur die alte Schreibweise ab und lieferte darum **für jedes Werkzeug jedes Servers** ein leeres Schema (18.08.2026: alle 31 leer). Dort inzwischen behoben — beide Schreibweisen werden abgefragt. *Wir haben nichts geändert; die HomeStation hat nur gelesen.* Unsere Seite war nie das Problem: `integrations/odysseus/aiimaging_mcp_server.py` und `src/aiimaging/mcp_schemas.py` liefern die Schemata seit jeher — direkt am Server gegengeprüft |
| A5 | `query_render` und `check_geometry` in `READ_ONLY_MCP_TOOLS` **beantragen** (`enqueue_render` ausdrücklich **nicht**) | 🟩 **erledigt** | 2026-09-10 | **belegt am Gerät:** `auf-20260826-48` (R4/R6), beendet **07.09.2026**. Beide stehen in der Liste — **seit dem 18.08.2026**, also acht Tage **vor** unserer Bitte, und ohne dass wir es wissen konnten: *«Der Auftragsteller hat keine Einsicht in dieses private Backend-Repo.»* `enqueue_render` ist korrekt draussen (es schreibt eine Auftragsdatei). *Ein erledigter Posten, den wir 23 Tage lang als offen geführt haben, weil wir nicht hinsehen konnten und nicht gefragt haben.* **Eine Lücke bleibt und ist weitergegeben:** `aiimaging_capabilities` fehlt in der Liste — von der HomeStation selbst als «vermutlich ein Versäumnis» gemeldet, beauftragt in `auftraege/offen/auf-20260910-101.json` (zweiter Teil). Unsere Seite: `src/aiimaging/werkzeuge.py` |
| A6 | Rezept «AI-Imaging» beantragen: Konfiguration → `check_geometry` (Gate) → `enqueue_render` → `query_render` | 🟥 **offen** | — | **Gemessen am 07.09.2026** (`auf-20260826-48`, R6): **17 Rezepte in `recipes.ts`, keines für `aiimaging`** — die Lane ist über Rezepte nicht erreichbar. Die HomeStation hat es ausdrücklich **nicht selbst umgesetzt**: *«gehört zur KosmoOrbit-Lane, nicht zu diesem Repo»*. **Bis zum 10.09.2026 zeigte dieser Posten damit auf einen Auftrag, der ihn nicht enthielt — beauftragt war er nie.** Jetzt beim richtigen Adressaten: `auftraege/offen/auf-20260910-102.json` (`cloud`), mit dem Vorschlag im Volltext und dem Hinweis, dass `enqueue_render` schreibt und nicht automatisch laufen darf. Unsere Seite: `src/aiimaging/werkzeuge.py` |
| A7 | Feldnamen gegen den vorgesehenen Vorgänger prüfen | 🟩 **halb** | 2026-09-10 | `contracts.LANE_FIELDS` und `mcp_schemas.pruefe_verdrahtbarkeit` belegen die Verdrahtbarkeit **rechnerisch**; am laufenden Cockpit gemessen ist sie **weiterhin nicht**. **Der Beleg ist am 10.09.2026 richtiggestellt worden:** `auf-20260826-58` hat A7 nicht gemessen, sondern nur **entsperrt** — die HomeStation sagt es selbst: *«Diese Sitzung hat das nur ENTSPERRT, aber die eigentliche A7-Messung … nicht durchgeführt.»* Seit A4 stehen die Schemata am Endpunkt vollständig da, damit ist die Messung jetzt **möglich**. Neu beauftragt: `auftraege/offen/auf-20260910-101.json` |
| A8 | Wo erscheinen Bild und QA-Wert? Im Cockpit gibt es keinen Ort dafür | 🟩 **erledigt** | 2026-09-09 | **belegt am Gerät:** `auf-20260826-52` (O1), gemessen vom UI-Worker gegen `kosmo-orbit 71b7f325`. KosmoVis ist dort eine **eigene Station mit eigenem Node-Graph** — kein Ausklapp eines fremden Cockpit-Knotens: `NodeCanvas.tsx` (2282 Zeilen), `KuratierFlaeche.tsx` (530), `KuratierInspektor.tsx` (185), `VisWorkspace.tsx` (170). Der Entwurf (`docs/OBERFLAECHE_KOSMOVIS.md`) hat die Entscheidung nicht ausgelöst — *sie stand dort vorher schon so.* **Der Ort existiert; was darin fehlt, führt A10** |
| A10 | Die Oberfläche selbst — Bedienelemente, Anzeige, die drei Zustände | 🟩 **halb** | 2026-09-09 | **belegt am Gerät:** `auf-20260826-52`, gemessen gegen `kosmo-orbit 71b7f325`, je Regel einzeln und mit Datei und Zeile — die Dateien liegen in **ihrem** Repo (`vis-jobs.ts`, `varianten-diff.ts`, `KuratierInspektor.tsx`, `NodeCanvas.tsx`) und darum ohne Pfad, damit dieser Beleg nicht auf unseren zeigt. **Regel 1 (kein wirkungsloses Bedienelement): erledigt** — `upscale` fest auf `false`, `style.refs` feste leere Liste, kein Stil-Regler. **Regel 2 (dreiwertige Anzeige): gemischt** — der Inspektor zeigt `bewertet / ohne-qa / widerrufen` mit ausdrücklichem Text, die Bildkachel in `NodeCanvas.tsx` zeigt bei fehlender QA **gar kein Abzeichen**: kein Falschurteil, aber auch nicht die dritte sichtbare Kategorie. **Regel 3 (Wert an seiner Bedingung): teilweise** — Treue und Samples stehen daneben, Auflösung und Backbone nicht, und **keiner der drei Vorbehalte** aus `aiimaging_capabilities` erscheint irgendwo. **Regel 4: zweigeteilt** — der QA-Vorbehalt am bestandenen Verdikt ist seit `69f2366a` an drei Stellen sichtbar, das breit gemeinte «acht statt zwölf Bilder je Kamera» ist nicht gebaut. *Die offenen Hälften laufen als U1–U9 in `docs/UI_BEFUNDE.md` weiter*; der Entwurf, gegen den gemessen wurde, ist `docs/OBERFLAECHE_KOSMOVIS.md` |
| A11 | **Ein bestandener Lauf ohne Bauwerk wird nicht wie jeder andere gezeigt** | 🟩 **erledigt** | 2026-09-11 | **belegt am Gerät:** `auf-20260827-62`, beantwortet am 03.09.2026. Der Vorbehalt steht an **drei** Stellen offen im DOM — Bildkachel (Häkchen bleibt, bekommt Warnzeichen und Warnfarbe, der **ungekürzte** Satz darunter), Kurations-Inspektor (eigene Meta-Zeile) und A/B-Vergleichstabelle (eigene Zeile unter dem QA-Verdikt). **Kein Aufklappen, keine Zeigergeste.** Vorher: *0 Treffer im ganzen Vis-Modul.* **Und die schwierigere Hälfte ist auch belegt:** Ohne `reason` erscheint **nichts** — drei Proben halten das Verschwinden fest, *«eine Warnung, die immer dasteht, wird nicht gelesen»*. Rot vor grün: 3 von 6 Proben rot mit zurückgestellten Dateien, 6 von 6 grün danach; die Proben prüfen **Wortgleichheit**, unser Satz wird weder gekürzt noch umformuliert. Unsere Seite: `src/aiimaging/kosmo_szene.py` (`als_ergebnis`, der Vertragsgrund). **Eine Ungenauigkeit unseres eigenen Auftragstexts haben sie dabei richtiggestellt:** Wir beschrieben die Bedingung als «`bestanden` wahr UND `paarurteil.bestanden` falsch» — `paarurteil.bestanden` ist aber ein Feld **unseres inneren Urteils**, nicht ihres Vertrags. Wer es dort als Schemafeld sucht, läuft in die Irre. Sie haben folgerichtig nichts nachgerechnet, sondern nur unseren Satz durchgereicht: *«das Tor bleibt bei euch, wir bauen es nicht nach»* |
| A12 | **Wer die Freigabe erteilt, gibt sie auch aus** — das Gate prüft die Form eines Tokens, nicht die Befugnis | 🟩 **gebaut, am Gerät unbestätigt** | 2026-09-09 | **belegt im Repo:** `jobs.TOKENBUCH` mit `token_ausgeben` / `token_befugt` / `token_entwerten`, sieben Proben in `tests/test_jobs.py`. **Die Prüfung ist eingebaut und AUS** (`freigeben(..., mit_buch=False)`): Es gibt niemanden, der Token ausgibt, und eingeschaltet wiese sie über Nacht jede bestehende Freigabe ab. Der Ausgeber gehört in die Oberfläche — beauftragt in `auftraege/offen/auf-20260909-99.json` (Adressat `ui`). Ursprung: `auf-vis-20260821-03` der HomeStation, 21.08.2026 |
| A9 | Die Registrierung nachweisen — sie liegt acht Tage und **ein Werkzeug** zurück | 🟩 **erledigt** | 2026-09-01 | **belegt am Gerät:** Seam-Health der HomeStation am **01.09.2026 um 06:49:35** — Server `aiimaging`, Kennung `d99fcf67`, **10 Werkzeuge**, `aiimaging_capabilities ok`. Geprüft **per echtem Tool-Call** und nicht am `connected`-Flag: Das ist dort nachweislich unzuverlässig (ein toter Server meldete `exit_code: 1` bei leerem stderr). Quelle: `auftraege/von-homestation/geraetebefunde-20260901.md`. *`auf-20260826-48` bleibt offen — R1, R2 und A6 messen anderes und sind damit nicht beantwortet.* |

*A9 stand 2026-08-19 nicht auf der Liste, weil die Registrierung damals als erledigt galt.
Sie war es auch: `id d99fcf67`, alle **drei** Werkzeuge antworteten (Sitzung 07, Kap. 26).
Seither ist `aiimaging_capabilities` dazugekommen und der Ausführungspfad — beides am
Gerät unbestätigt. **Eine Behauptung, die stimmte, als sie geschrieben wurde.**
`README.md` trug bis zum 26.08. den entgegengesetzten Fehler und sagte «Registrierung
nicht ausgeführt».*

*Erledigt am 01.09.2026, und der Weg dahin ist der Punkt: Nicht eine Datei im Repo hat
es belegt, sondern eine Messung am Gerät, die von dort gemeldet wurde. **Vierzehn Tage lang
war die Frage «ist es registriert?» hier nicht zu beantworten** — nicht, weil niemand nachsah,
sondern weil sie hier nicht nachsehbar ist.*

---

## Weg B — über die Brücke (Szenenvertrag)

| # | Posten | Zustand | Seit | Beleg / treibender Auftrag |
|---|---|---|---|---|
| B1 | Unseren Vertrag gegen `kosmovis.render-scene/v1` halten, an **einer** Stelle übersetzen | 🟩 **erledigt** | 2026-08-19 | **belegt im Repo:** `src/aiimaging/kosmo_szene.py` (`lies_szene`), `src/aiimaging/kosmo_naht.py` |
| B2 | Kameravertrag angleichen (`name`/`position`/`target`/`fov` gegen `blick_auf` und Brennweite in mm) | 🟩 **erledigt** | 2026-08-19 | **belegt im Repo:** `kosmo_szene.kamera_zu_spec`, `spec_zu_kamera`, `brennweite_zu_fov` |
| B3 | `kosmovis.render-result/v2` erzeugen, mit `spearman` und `geom_iou` einzeln | 🟩 **erledigt** | 2026-08-19 | **belegt im Repo:** `kosmo_szene.als_ergebnis` (`geometry_fidelity`, `spearman`, `geom_iou`, `threshold`) |
| B4 | **Der Arbeiter fehlt auf beiden Seiten** — die Brücke legt Dateien ab und wartet | 🟩 **erledigt** | 2026-08-22 | **belegt am Gerät:** Messung 27.08.2026, 18:53:42 bestellt → 18:54:11 aufgegriffen, Blender lief. Code dazu: `src/aiimaging/abholer.py`, `tools/abholen.py`, `betrieb/kosmo-abholer.{service,timer}`. *Bis 28.08. stand hier `auf-20260822-31` — das ist ein Weiterleitungsvermerk und keine Antwort; der Beleg war falsch zitiert, nicht falsch* |
| B5 | QA **je Kamera** ausweisen und die Verzeichniskonvention bedienen | 🟩 **halb** | 2026-09-11 | Je Kamera gemessen und in `befund.json` abgelegt. **Der Engpass hat am 03.09.2026 die Seite gewechselt, und wir haben es acht Tage lang nicht gemerkt:** Ihr Vertrag trägt seither `qa_je_kamera` — optionales Array von `{kamera, geometry?, style?}`, `kamera` ist Pflicht je Eintrag, *«der bestehende `qa`-Block bleibt BYTE-IDENTISCH»* (`auf-20260826-49`, Owner-Entscheid, V2). **Wir senden es seit dem 11.09.2026** — und zwar bis an die Naht verdrahtet, nicht nur gebaut: `kosmo_szene.als_ergebnis(je_kamera=…)`, durchgereicht von `bruecke.schreibe_ergebnis` und `eigene_quelle.schreibe_ergebnis`, gefüllt in `abholer._qa_je_kamera_eintraege`. Der Geometrieblock je Kamera wird **nicht nachgebaut**: Die Funktion ruft sich je Kamera selbst auf, damit ein Block je Kamera dasselbe bedeutet wie der des Laufs. Eine **nicht gemessene** Kamera trägt nur ihren Namen — ein Block mit `geometry_fidelity: null` läse sich als durchgefallen. Elf Proben. **Halb und nicht erledigt, weil eines ungeklärt ist:** Ihr Entscheid sagt nicht, **wo** das Feld steht. Wir legen es **neben** den `qa`-Block — ein Schluss aus ihrem eigenen Satz *«der `qa`-Block bleibt byte-identisch»*, denn ein zusätzlicher Schlüssel darin wäre genau das nicht. Rückfrage: `auftraege/offen/auf-20260911-105.json` |
| B6 | Varianten: *n* Bilder je Lauf | 🟩 **verworfen** | 2026-09-11 | **Vom Cloud-Worker ausdrücklich abgelehnt** (`auf-20260826-49`, Owner-Entscheid 03.09.2026, V3): *«NEIN — ausdrücklich.»* Begründung: Varianten je Kamera verlangten zuerst eine Bedeutungsfestlegung (was ist eine Variante, wie viele je Kamera, wonach wählt der Benutzer), und *«wir haben heute keinen Ort in der Oberfläche, an dem ein Benutzer zwischen Varianten wählt — ohne den wäre jede Festlegung geraten. Ihr habt uns Raten ausdrücklich untersagt.»* Dazu: *«Ihr könnt den Vorbau dafür streichen»* — bei uns gibt es keinen: `src/aiimaging/varianten.py` misst die Startwertstreuung und ist etwas anderes. **Sollte es sich ändern, melden sie sich von selbst; wir müssen nicht nachfragen.** |
| B7 | Den Treue-Regler `render.faithful` durchreichen | 🟩 **erledigt** | 2026-08-19 | **belegt im Repo:** `kosmo_szene.lies_szene` bildet ihn auf `controlnet_staerke` ab und sagt es in der Warnung |
| B8 | Ein über den **MCP-Einlass** bestellter Render wird auch ausgeführt | 🟩 **erledigt** | 2026-08-27 | **belegt am Gerät:** Messung 27.08.2026, 18:53:40 Ablage leer → 18:53:42 bestellt → 18:54:11 aufgegriffen, Blender lief. Code dazu: `src/aiimaging/eigene_quelle.py`, `abholer.hole_einen(quelle=…)`, `tools/abholen.py --eigener-store`, `tests/test_betriebseinheiten.py` |

*Das Datum von B8 ist am 2026-08-27 von 26.08. auf 27.08. **zurückgesetzt** worden, und
zwar nach einer Messung am Gerät. Am 26.08. bekam `betrieb/kosmo-abholer.service` den
Schalter `--eigener-store`, und der Posten wurde als erledigt verbucht. Die wirklich
eingebaute Nutzereinheit stammte aber vom 20.08. und kannte ihn nicht — sechs Tage lang
blieb jeder über den MCP-Einlass bestellte Render liegen, während hier stand, es sei
behoben.*

*Der Wächter über diesem Blatt konnte das nicht sehen: Er prüft, ob ein als erledigt
geführter Posten einen **Beleg nennt, den es gibt**, und den gab es — die Datei lag im
Repo und trug den Schalter.* **Eine Datei im Repo belegt, was jemand geschrieben hat,
nicht was auf dem Gerät läuft.** *Ursache war der Platzhalter `<nutzer>`, der jede
Installation zur Handkopie machte; seit dem 27.08. lösen die Einheiten das
Heimatverzeichnis über systemds `%h` auf, und `tests/test_betriebseinheiten.py` hält
eingebaut und eingecheckt gegeneinander. Belegt ist der Posten seither an einem Auftrag,
der wirklich angekommen ist, nicht an einem Dienst, der antwortet.*

*B8 stand 2026-08-19 nicht auf der Liste, und das ist der unangenehmste Eintrag dieses
Blatts: Es fiel niemandem auf, dass die beiden Wege sich hier kreuzen. Weg A legte einen
Auftrag ab, Weg B hatte den einzigen Ausführer — und niemand las die Ablage von A. Ein
Knoten in KosmoOrbit konnte einen Render bestellen, der mit Freigabe auf `queued` ging und
dort blieb.*

---

## Weg C — der Ausführungspfad auf der HomeStation

**Warum dieser Abschnitt seit dem 26.08.2026 dazugehört.** Wege A und B beschreiben, wie
KosmoVis in einem **fremden** Repo erscheint. Es gibt aber einen dritten Weg, auf dem
unser Code in Betrieb geht, und er lief bisher ohne Buchführung: Die HomeStation führt
`tools/homeworker.py` und `tools/abholen.py` **aus diesem Repo** aus. Ein `git pull` dort
ändert, was gerechnet wird — ohne dass irgendwo ein Posten umspringt.

*Das ist dieselbe Lücke wie oben, nur schneller: Bei A und B weiss man wenigstens, dass
etwas fehlt. Hier sieht ein veralteter Stand aus wie der aktuelle.*

**Und der 27.08.2026 hat gezeigt, wie dieser Weg schiefgeht.** Sechs Tage lang stand
`B8` als erledigt im Blatt, weil die eingecheckte Diensteinheit den nötigen Schalter trug —
die **installierte** stammte vom 20.08. und kannte ihn nicht. Ursache war ein
Literal-Platzhalter für das Heimatverzeichnis, der jede Installation zur Handkopie machte.

> **Eine Datei im Repo belegt, was jemand geschrieben hat, nicht was auf dem Gerät läuft.**

*Seit dem 27.08. lösen die Einheiten das Heimatverzeichnis über systemds eigenes `%h` auf —
nichts mehr von Hand abzuschreiben, und trotzdem kein Name im Repo —, und
`tests/test_betriebseinheiten.py` hält eingebaut und eingecheckt gegeneinander. Auf einem
Gerät ohne Installation überspringt er, statt grün zu behaupten.*

| # | Posten | Zustand | Seit | Beleg / treibender Auftrag |
|---|---|---|---|---|
| C1 | Der Abholer läuft dort als Dienst | 🟩 **erledigt** | 2026-08-22 | **belegt am Gerät:** Messung 27.08.2026, 18:53:40 Ablage leer → 18:53:42 `queued` → 18:54:11 `gesehen: 1`, Status `running`. Einheiten: `betrieb/kosmo-abholer.{service,timer}`. *Bis 28.08. stand hier `auf-20260822-31` — ein Weiterleitungsvermerk, keine Antwort* |
| C7 | **Der Homeworker hat einen Takt** — bis dahin stiess ihn nichts an | 🟩 **verworfen** | 2026-09-11 | **Vom Gerät abgelehnt, mit drei gemessenen Gründen** (`auf-20260907-83`): (1) Der Takt käme nicht von der Stelle — zwei Takte auf einer Kopie wählten beide Male denselben Auftrag (`auf-20260907-81`) und endeten beide Male mit `fehler`; `fehler` zählt als *gerechnet, nicht beantwortet*, also bleibt der Rang, also wählt der nächste Takt dasselbe. (2) 288 Neuschreibungen je Tag bei 5-Minuten-Takt. (3) Der Committer war nicht der einzige und nicht der grösste Grund — er war der, den man sehen konnte. *Gebaut ist es (`betrieb/kosmo-worker.{sh,service,timer}`, `tools/homeworker.py --hoechstens`); eingebaut wird es nicht.* **Am 11.09.2026 von «entschieden, nicht gebaut» auf «verworfen» umgestellt:** Der alte Zustand hiess zweierlei — bei `A8` *«entschieden ist, WIE»* (ein offener Posten mit Richtung), hier *«entschieden ist, DASS NICHT»* (ein fertiger). Unter einem Wort stand dieser Posten für immer im Rückstand, an etwas, das niemand je bauen wird. |
| C2 | Die HomeStation hat den Stand vom Abend des 26.08. gezogen | 🟩 **erledigt** | 2026-08-27 | **belegt am Gerät:** nicht an einer Meldung, sondern an einem Nebenprodukt: Die 85 Abstürze von `tools/abholen.py` (Sitzung 14, `docs/sitzungen/2026-08-27_sitzung-14.md`) beginnen um 17:55:39, also genau mit dem Holen der 41 Commits. *Was der Stand dort **tut**, ist damit nicht bestätigt — das fragt `auf-20260826-57.json` (V1–V5), und C3 bis C8 hängen weiter daran.* |
| C3 | `bestanden` ist dreiwertig — `null` heisst *nicht beurteilbar* | 🟩 **erledigt** | 2026-09-09 | **belegt am Gerät:** `auf-20260826-57`, beendet **06.09.2026**. Die HomeStation schreibt dort ausdrücklich: *«Alle vier im Auftrag beschriebenen Verhaltensänderungen — Kleene-Logik für `bestanden`, Maskenweg beim Homeworker, gerichtete Polarität am Tor, Katalogbeweis für Gelände — sind am Gerät bestätigt und funktionieren wie beschrieben.»* **Und der Lauf hat den dritten Wert geliefert, nach dem gar nicht gefragt war:** `bestanden: false` statt `true` oder `null` — weil der Maskenweg lief und ein eigenes Urteil hatte (Kantenanteil 4,1 % gegen Schwelle 20 %). *`null` wäre nur gekommen, wenn er nicht gelaufen wäre.* Genau das ist die Kleene-Logik, in einem Fall, den der Auftragstext nicht durchgespielt hatte. Gebaut in `tiefenschaetzer.qa_gegen_soll`, `gate.gesamturteil` |
| C4 | Der Maskenweg wird im Homeworker gefahren | 🟩 **erledigt** | 2026-09-09 | **belegt am Gerät:** `auf-20260826-57`, beendet **06.09.2026**. Die HomeStation schreibt dort ausdrücklich: *«Alle vier im Auftrag beschriebenen Verhaltensänderungen — Kleene-Logik für `bestanden`, Maskenweg beim Homeworker, gerichtete Polarität am Tor, Katalogbeweis für Gelände — sind am Gerät bestätigt und funktionieren wie beschrieben.»* Für diesen Posten misst V2: **alle vier Grössen tragen Zahlen, keine ist `None`** — `rho_maske` −0,9939 (gerichtet 0,9939, Polarität −1), `kante` 0,00063, `kantenanteil` 0,0410 gegen Zufall 0,0500, `paarurteil` gefüllt. *Bis dahin standen sie in jedem Lauf der HomeStation auf `None`.* Gebaut in `tools/homeworker.py`, `maske.maske_aus_bericht` |
| C5 | Die gemessene Polarität kommt am Tor an | 🟩 **erledigt** | 2026-09-09 | **belegt am Gerät:** `auf-20260826-57`, beendet **06.09.2026**. Die HomeStation schreibt dort ausdrücklich: *«Alle vier im Auftrag beschriebenen Verhaltensänderungen — Kleene-Logik für `bestanden`, Maskenweg beim Homeworker, gerichtete Polarität am Tor, Katalogbeweis für Gelände — sind am Gerät bestätigt und funktionieren wie beschrieben.»* V3 am Gerät: Methode `sqrt(max(0, polaritaet · spearman) · geom_iou)`, **`polaritaet_zeichen: -1`**, gerichtete Rechnung aktiv. *Vorher war das Zeichen gerechnet und nirgends nachgesehen.* Gebaut in `tiefenschaetzer.gemessenes_zeichen` |
| C6 | `gelaende_erwartet` ist aus dem Auftrag steuerbar | 🟩 **erledigt** | 2026-09-09 | **belegt am Gerät:** `auf-20260826-57`, beendet **06.09.2026**. Die HomeStation schreibt dort ausdrücklich: *«Alle vier im Auftrag beschriebenen Verhaltensänderungen — Kleene-Logik für `bestanden`, Maskenweg beim Homeworker, gerichtete Polarität am Tor, Katalogbeweis für Gelände — sind am Gerät bestätigt und funktionieren wie beschrieben.»* V1 zeigt den Katalogbeweis in Worten der HomeStation: *«5 benannte Einträge geprüft, keiner nach Gelände … `IfcSite` ist die genormte Klasse»* — der Katalogweg greift, ohne dass jemand etwas von Hand angeben muss. Gebaut in `tools/homeworker.py` (liest `params.gelaende_erwartet`), `maske.ist_ifc_klassenkatalog` |
| C8 | **Der Widerspruch zwischen Score und Maskenweg steht im Befund** | 🟩 **gebaut, am Gerät unbestätigt** | 2026-08-27 | `abholer.befund_kurz`, `kosmo_szene` — Owner-Entscheid 26.08.: erst kalibrieren, bis dahin sichtbar machen. Anlass gemessen: verschwundenes Bauwerk, Score 0.951, `rho_maske` −0.018. Kalibrierung: `auftraege/offen/auf-20260827-61.json`. **Bestätigung am Gerät steht weiterhin aus, und der Grund ist am 09.09.2026 gemessen worden:** In `auf-20260826-57` stand `score: null` — es gab keinen Widerspruch, also erschien die Zeile nicht, also belegt der Lauf nichts. *Ein Fall, der nicht eintritt, bestätigt keine Anzeige.* Neu beauftragt an einem Fall, der ihn enthält: `auftraege/offen/auf-20260909-100.json` |
| C9 | Die Paarschwellen sind kalibriert, nicht abgelesen | 🟥 **offen** | — | `auftraege/offen/auf-20260827-61.json` — `PAAR_RHO_SCHWELLE` 0.80 aus **sieben** Fällen einer Szene, `PAAR_KANTENANTEIL_SCHWELLE` 0.20 beim Vierfachen des Zufalls. Bedingung für das zweite Tor. **Rechenwerkzeug und Obergrenze liegen** (`aiimaging.paarschwellen`, `tools/paarschwellen.py`, `tools/studie_paarmasse.py`, 27.08.): ρ trennt mit perfekten Karten sauber zwischen 0.6169 und 0.9282, der Kantenanteil **gar nicht**. **Die Fälle unter Schätzerrauschen sind da (`auf-20260907-81`, 08.09.2026, 176 Zeilen, echter Schätzer) — und sie kehren den Befund um:** Frontal gibt es **kein fehlerfreies Fenster mehr** (höchster schlechter 0,9957 über niedrigstem guten 0,1426); diagonal trennt weiter (0,5906 < t ≤ 0,9468). Die 0,80 sperrt **11 statt 5** gute frontale Fälle — darunter auf zwei von acht Ansichten den treuen Blender-Render selbst — **und lässt erstmals 2 schlechte durch**. Mechanismus gemessen: 21,7 % der Maskenpunkte holen ihren Wert von ausserhalb des Umrisses; in der Soll-Karte ist das die Hintergrundmarke 1e10 (eine Konstante ohne Rangfolge), in der Schätzung stehen dort gewöhnliche Werte, und über diese Punkte allein korreliert der verrutschte Streifen mit +0,9873. *Was die perfekte Karte an einer unendlichen Kante fängt, glättet der Schätzer weg.* **Eine Kalibrierung trägt diese Messung ausdrücklich nicht** — das Bild kommt aus Blender, nicht aus dem Bildmodell |
| C10 | **`geom_iou` weist aus, wie viel davon der Szene gehört** | 🟩 **gebaut, am Gerät unbestätigt** | 2026-08-28 | `geometrie_qa._iou_ohne_boden`, `tiefenschaetzer.qa_gegen_soll` (`geom_iou_norm`), `abholer.befund_kurz`. Owner-Entscheid 28.08.: der Score bleibt unangetastet, der normierte Wert steht daneben. Anlass: Ein konstantes Bild bekommt **exakt** den Vordergrundanteil (0.1104 · 0.1729 · 0.5297, auf volle Gleitkommagenauigkeit). **Bestätigung am Gerät steht weiterhin aus:** `auf-20260826-57` lief mit `score: null`, und ob `geom_iou_norm` neben dem Score erscheint, ist daraus nicht ablesbar. Neu beauftragt: `auftraege/offen/auf-20260909-100.json` |
| C11 | **Die Kamera steht waagrecht — der Entscheid vom 23.08. gilt jetzt auch im Runner** | 🟩 **erledigt** | 2026-09-09 | **belegt am Gerät:** `auf-20260828-65`, beendet **28.08.2026 um 11:19:01**. Zwei Läufe, beide `kamera_modus: shift`, **`kamera_neigung_grad: 0.0`** — einmal an der synthetischen Hochbaugeometrie (Auge und Blickziel beide auf 1,45 m, also waagrecht) und einmal am echten Bestandsmodell mit 4771 Bauteilen. *Vorher stand jeder Lauf auf `gekippt`, weil der Runner die Bibliothek überstimmte.* Gebaut in `src/aiimaging/runners/blender_depth_stage.py`, bewacht von `tests/test_kameramodus_vorgabe.py` |
| C12 | **Der Demolauf macht ein Bild auf 1,70 m Augenhöhe** | 🟩 **erledigt** | 2026-09-09 | **belegt am Gerät:** `auf-20260828-65` (V0), beendet **28.08.2026 um 11:19:01** — `augenhoehe_ueber_huellbox_unterkante_m: 1.7`, Antwort **ja**, dazu `kamera_weg: abgeleitet` statt `rueckfall`, `sSE`, 35 mm, waagrecht. *Vorher forderte der Homeworker gar keine Kamera an, und der Runner stellte seine Notkamera mit 50 mm.* Gebaut in `tools/homeworker.py` (`VORGABE_KAMERA`, `_KAMERA_PARAMS`), bewacht von `tests/test_homeworker.py`. **Ein Vorbehalt bleibt, und er steht im Plan** («Der Geländestand ist aus einer glb nicht zu erfahren»): am echten Modell mit Untergeschoss steht die Kamera damit im Keller — gemessen 3,238 m unter dem Erdgeschossfussboden, 12 mm über dem Untergeschossfussboden. *Das ist ein Befund über den Rückfall, nicht über diesen Posten* |
| C13 | **Der Homeworker liest, für wen ein Auftrag ist** | 🟩 **erledigt** | 2026-09-10 | **belegt am Gerät:** `auf-20260828-64` (V1), beendet **28.08.2026 um 11:10:55** — `unausfuehrbare_auftraege_vorher: 9`, **`nachher: 0`**. Der Filter läuft dort: `EIGENER_WORKER='local'`, ein fremder Auftrag wird **weder ausgeführt noch abgelehnt** (*«eine Ablehnung zählte als Antwort und wäre schlimmer als Schweigen»*), ein fehlendes `worker`-Feld gilt als fremd. Vorher wurde das Feld nirgends gelesen — neun Aufträge an `cloud`/`ui` wären grün-leer geschlossen worden. Corroboriert durch `auf-20260828-65` acht Minuten später: nur eigene Aufträge gerechnet. Gebaut in `tools/homeworker.py` (`EIGENER_WORKER`), bewacht von `tests/test_homeworker.py`. *Die Auflage «muss vor dem Takt installiert sein» ist gegenstandslos geworden: Der Takt wird nicht gebaut (`C7`).* |
| C14 | **Drei Angaben, die gelesen und nie verwendet wurden** | 🟩 **erledigt** | 2026-09-09 | **belegt am Gerät**, und der Beleg liegt in der **Reihenfolge zweier Zeitstempel**: `auf-20260828-66` meldet die drei Fixes um **11:10:55**, `auf-20260828-65` läuft um **11:19:01** — also auf dem behobenen Stand. In dessen Ergebnis ist beides sichtbar: `erzeugen_mit` wirkt (die Geometrie ist «synthetischer Hochbau (`--hochbau`)», vorher erreichte die Flagge den Aufruf nie), und der **Kamerablock steht in `messwerte`** (vorher war V0 aus dem Ergebnis nicht beantwortbar). Die dritte Angabe ist **repo-seitig belegt**: `ARTEN` wird in `tools/homeworker.py` geprüft, Probe `test_eine_unbekannte_art_laeuft_nicht_still_als_multipass` in `tests/test_homeworker.py` — eine unbekannte Art lief vorher still als Multipass |
| C15 | **`herkunft.py` kennt keine Kennung `kosmoorbit`** | 🟥 **offen** | — | `auftraege/offen/auf-20260902-73.json` — messen kann es nur, wer eine echte KosmoOrbit-Ausgabe hat. **Der Auftrag sprengt meinen eigenen Deckel** (`local` trägt 21, die Selbstbindung liegt bei 8), und das ist bewusst: Ein Posten ohne Adressaten wird nie eingebaut, und diese Hausregel des Owners sticht meine eigene Bremse. Er hat darum den letzten Rang. Die HomeStation hat den Posten am 02.09.2026 ausdrücklich offen gelassen (`auftraege/von-homestation/auf-vis-20260902-17.md`, V17c) mit der richtigen Begründung: Dass die glb aus KosmoOrbit Y-up ist, hat sie im **Quelltext des Exporters gelesen**, nicht an einer **Datei gemessen**. *Eine Herkunftstabelle ist kein Ort für eine Lesart: Sie sagt einem Betrachter, wie er die Datei zu drehen hat; steht dort eine Vermutung, dreht er falsch und niemand sieht es der Zeile an.* Genau dieser Unterschied war am 01.09. teuer — ein Achsenbruch, bei dem die Geometrie gedreht wurde und die Kamera nicht |

**Der unangenehmste Eintrag ist C7, und er lag auf unserer Seite.** Der Abholer hat seit
dem 22.08. einen Takt; der Homeworker hatte keinen. Sein Ritus war von Hand — `git pull`,
laufen lassen, `git add && commit && push` —, und solange niemand tippte, lagen Aufträge
beliebig lange. Am 26.08. waren es **siebzehn, der älteste drei Tage**. *Das ist der
Unterschied zwischen «beauftragt» und «wird auch gemacht».*

**Und C2.** Eine Verhaltensänderung, die über git ankommt, hat
keine Ansage — und `bestanden: null` sieht auf der anderen Seite aus wie ein Fehler, wenn
niemand gesagt hat, dass es einer sein soll. `auf-57` sagt es, bevor gezogen wird, und
bittet um **einen** Lauf zur Bestätigung.

---

## Ein Nachtrag vom selben Abend

Die HomeStation meldet für ihr zweites Modell einen Geometriewert von **0.7177** bzw.
**0.6804** — beide über der Schwelle 0.65. Ob das den stehenden Vorbehalt *«ein Bild, das
die Schwelle besteht, gibt es noch nicht»* umwirft, hängt daran, **auf welcher Stufe**
gemessen wurde; am Beauty-Pass liegt |spearman| bei 0.990, am Bild des Bildmodells bei
0.005, und 0.73 liegt dazwischen. Gefragt in `auftraege/offen/auf-20260826-50.json`. Bis
zur Antwort bleibt der Satz im README stehen.

## Was dieses Blatt nicht sagt

* **Ob ein Posten gut gelöst ist.** Es sagt, ob er getan ist. Die Güte steht in den
  Tests und Befunden, auf die die Belege zeigen.
* **Welchen Weg die Oberfläche nehmen wird.** Das ist Frage 4 des Übergabeblatts und
  unbeantwortet. Beide Wege werden tragfähig gehalten, damit die Antwort eine
  Entscheidung sein kann und kein Sachzwang.
