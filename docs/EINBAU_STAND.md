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
| A4 | Klären, warum `/api/mcp/tools` keine Schemata durchreicht | 🟥 **offen** | — | `auftraege/offen/auf-20260826-58.json` — braucht einen Blick ins Odysseus-Backend, den nur die HomeStation hat. *Stand bis zum 26.08.2026 als «niemand» da; unter dem Owner-Auftrag desselben Tages ist das keine zulässige Angabe mehr* |
| A5 | `query_render` und `check_geometry` in `READ_ONLY_MCP_TOOLS` **beantragen** (`enqueue_render` ausdrücklich **nicht**) | 🟥 **offen** | — | `auftraege/offen/auf-20260826-48.json` |
| A6 | Rezept «AI-Imaging» beantragen: Konfiguration → `check_geometry` (Gate) → `enqueue_render` → `query_render` | 🟥 **offen** | — | `auftraege/offen/auf-20260826-48.json` |
| A7 | Feldnamen gegen den vorgesehenen Vorgänger prüfen | 🟩 **halb** | 2026-08-18 | `contracts.LANE_FIELDS` und `mcp_schemas.pruefe_verdrahtbarkeit` belegen die Verdrahtbarkeit **rechnerisch**; am laufenden Cockpit gemessen ist sie nicht. Hängt an A4 und wird mit ihm getrieben: `auftraege/offen/auf-20260826-58.json` (Schritt 4) |
| A8 | Wo erscheinen Bild und QA-Wert? Im Cockpit gibt es keinen Ort dafür | 🟩 **entschieden, nicht gebaut** | 2026-08-26 | In der **KosmoVis-Fläche**, nicht als neuer Anzeigetyp im fremden Knotenrahmen — der innere Graph bekommt eine innere Oberfläche. Entwurf: `docs/OBERFLAECHE_KOSMOVIS.md`; gebaut wird er über `auftraege/offen/auf-20260826-52.json` |
| A10 | Die Oberfläche selbst — Bedienelemente, Anzeige, die drei Zustände | 🟥 **offen** | — | Entwurf steht (`docs/OBERFLAECHE_KOSMOVIS.md`), Bau beauftragt in `auftraege/offen/auf-20260826-52.json`. Der Auftrag trägt den Entwurf **im Volltext** — die Hausregel verbietet ein «siehe Dokument XY» |
| A11 | **Ein bestandener Lauf ohne Bauwerk wird nicht wie jeder andere gezeigt** | 🟥 **offen** | — | `auftraege/offen/auf-20260827-62.json` — der Vertragsgrund trägt den Satz seit 27.08. (`kosmo_szene`). Solange die Oberfläche ihn nicht mitträgt, sieht ein Bild ohne Bauwerk dort aus wie ein geprüftes |
| A9 | Die Registrierung nachweisen — sie liegt acht Tage und **ein Werkzeug** zurück | 🟥 **offen** | — | `auftraege/offen/auf-20260826-48.json` |

*A9 stand 2026-08-19 nicht auf der Liste, weil die Registrierung damals als erledigt galt.
Sie war es auch: `id d99fcf67`, alle **drei** Werkzeuge antworteten (Sitzung 07, Kap. 26).
Seither ist `aiimaging_capabilities` dazugekommen und der Ausführungspfad — beides am
Gerät unbestätigt. **Eine Behauptung, die stimmte, als sie geschrieben wurde.**
`README.md` trug bis zum 26.08. den entgegengesetzten Fehler und sagte «Registrierung
nicht ausgeführt».*

---

## Weg B — über die Brücke (Szenenvertrag)

| # | Posten | Zustand | Seit | Beleg / treibender Auftrag |
|---|---|---|---|---|
| B1 | Unseren Vertrag gegen `kosmovis.render-scene/v1` halten, an **einer** Stelle übersetzen | 🟩 **erledigt** | 2026-08-19 | **belegt im Repo:** `src/aiimaging/kosmo_szene.py` (`lies_szene`), `src/aiimaging/kosmo_naht.py` |
| B2 | Kameravertrag angleichen (`name`/`position`/`target`/`fov` gegen `blick_auf` und Brennweite in mm) | 🟩 **erledigt** | 2026-08-19 | **belegt im Repo:** `kosmo_szene.kamera_zu_spec`, `spec_zu_kamera`, `brennweite_zu_fov` |
| B3 | `kosmovis.render-result/v2` erzeugen, mit `spearman` und `geom_iou` einzeln | 🟩 **erledigt** | 2026-08-19 | **belegt im Repo:** `kosmo_szene.als_ergebnis` (`geometry_fidelity`, `spearman`, `geom_iou`, `threshold`) |
| B4 | **Der Arbeiter fehlt auf beiden Seiten** — die Brücke legt Dateien ab und wartet | 🟩 **erledigt** | 2026-08-22 | **belegt am Gerät:** `auf-20260822-31` (beantwortet) — Code dazu: `src/aiimaging/abholer.py`, `tools/abholen.py`, `betrieb/kosmo-abholer.{service,timer}` |
| B5 | QA **je Kamera** ausweisen und die Verzeichniskonvention bedienen | 🟩 **halb** | 2026-08-23 | Je Kamera gemessen und in `befund.json` abgelegt; der **Vertrag** trägt weiterhin **ein** QA je Lauf (das schlechteste). Ein QA-Block je Kamera ist ihre Vertragsänderung — `auftraege/offen/auf-20260826-49.json` |
| B6 | Varianten: *n* Bilder je Lauf | 🟥 **offen** | — | Weder unsere Kette noch der fremde Vertrag kennen sie. `auftraege/offen/auf-20260826-49.json` |
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
| C1 | Der Abholer läuft dort als Dienst | 🟩 **erledigt** | 2026-08-22 | **belegt am Gerät:** `auf-20260822-31` (beantwortet) und die Ergebnisse danach; Einheiten: `betrieb/kosmo-abholer.{service,timer}` |
| C7 | **Der Homeworker hat einen Takt** — bis dahin stiess ihn nichts an | 🟩 **gebaut, am Gerät unbestätigt** | 2026-08-26 | `betrieb/kosmo-worker.{sh,service,timer}`, `tools/homeworker.py --hoechstens`; Installation: `auftraege/offen/auf-20260826-59.json` |
| C2 | Die HomeStation hat den Stand vom Abend des 26.08. gezogen | 🟩 **erledigt** | 2026-08-27 | **belegt am Gerät:** nicht an einer Meldung, sondern an einem Nebenprodukt: Die 85 Abstürze von `tools/abholen.py` (Sitzung 14, `docs/sitzungen/2026-08-27_sitzung-14.md`) beginnen um 17:55:39, also genau mit dem Holen der 41 Commits. *Was der Stand dort **tut**, ist damit nicht bestätigt — das fragt `auf-20260826-57.json` (V1–V5), und C3 bis C8 hängen weiter daran.* |
| C3 | `bestanden` ist dreiwertig — `null` heisst *nicht beurteilbar* | 🟩 **gebaut, am Gerät unbestätigt** | 2026-08-26 | `tiefenschaetzer.qa_gegen_soll`, `gate.gesamturteil` — Bestätigung über `auftraege/offen/auf-20260826-57.json` |
| C4 | Der Maskenweg wird im Homeworker gefahren | 🟩 **gebaut, am Gerät unbestätigt** | 2026-08-26 | `tools/homeworker.py`, `maske.maske_aus_bericht` — bis dahin standen `rho_maske`, `kante`, `paarurteil` in **jedem** ihrer Läufe auf `None`. Bestätigung: `auftraege/offen/auf-20260826-57.json` (V2) |
| C5 | Die gemessene Polarität kommt am Tor an | 🟩 **gebaut, am Gerät unbestätigt** | 2026-08-26 | `tiefenschaetzer.gemessenes_zeichen` — an den 14 bekannten Läufen ändert sich kein Urteil, gerechnet. Bestätigung: `auftraege/offen/auf-20260826-57.json` (V3, V5) |
| C6 | `gelaende_erwartet` ist aus dem Auftrag steuerbar | 🟩 **gebaut, am Gerät unbestätigt** | 2026-08-26 | `tools/homeworker.py` liest `params.gelaende_erwartet`; über IFC-Klassennamen greift `maske.ist_ifc_klassenkatalog` ohnehin. Bestätigung: `auftraege/offen/auf-20260826-57.json` (V1) |
| C8 | **Der Widerspruch zwischen Score und Maskenweg steht im Befund** | 🟩 **gebaut, am Gerät unbestätigt** | 2026-08-27 | `abholer.befund_kurz`, `kosmo_szene` — Owner-Entscheid 26.08.: erst kalibrieren, bis dahin sichtbar machen. Anlass gemessen: verschwundenes Bauwerk, Score 0.951, `rho_maske` −0.018. Kalibrierung: `auftraege/offen/auf-20260827-61.json`; Bestätigung am Gerät: `auftraege/offen/auf-20260826-57.json` |
| C9 | Die Paarschwellen sind kalibriert, nicht abgelesen | 🟥 **offen** | — | `auftraege/offen/auf-20260827-61.json` — `PAAR_RHO_SCHWELLE` 0.80 aus **sieben** Fällen einer Szene, `PAAR_KANTENANTEIL_SCHWELLE` 0.20 beim Vierfachen des Zufalls. Bedingung für das zweite Tor. **Rechenwerkzeug und Obergrenze liegen** (`aiimaging.paarschwellen`, `tools/paarschwellen.py`, `tools/studie_paarmasse.py`, 27.08.): ρ trennt mit perfekten Karten sauber zwischen 0.6169 und 0.9282, der Kantenanteil **gar nicht**. Es fehlen nur noch die gemessenen Fälle unter Schätzerrauschen |

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
