# Der Weg hinein — Stand

**Wozu dieses Blatt.** `docs/COCKPIT_BESTAND_2026-08-19.md` §4 hat am 19.08.2026 den
vollständigen Weg aufgelistet, auf dem KosmoVis in KosmoOrbit erscheint: acht Posten über
das Cockpit (A1–A8), sieben über die Brücke (B1–B7). **Danach hat niemand Buch geführt.**
Sieben Tage später waren mehrere Posten still erledigt, mehrere still noch offen, und
niemand konnte sagen, welche.

Das ist dieselbe Sorte Lücke, die dieses Projekt im Code jagt — eine Aufstellung, die
stimmte, als sie geschrieben wurde. Sie steht hier darum mit **Datum und Beleg**, und
`tests/test_einbau_stand.py` hält sie: Jeder erledigte Posten nennt einen Beleg, den es
gibt; jeder offene nennt einen Auftrag oder ausdrücklich «niemand».

**Erledigtes wird abgehakt, nicht gelöscht** (Hausregel).

**Legende:** 🟩 = liegt in **unserem** Repo · 🟥 = liegt in einem **fremden** Repo, dort
wird ohne Rückfrage nichts geändert.

---

## Weg A — über das Cockpit (MCP-Knoten)

| # | Posten | Zustand | Seit | Beleg / treibender Auftrag |
|---|---|---|---|---|
| A1 | `mcp<2` festschreiben — der Server ist gegen die 1.x-Dekoratorschnittstelle geschrieben | 🟩 **erledigt** | 2026-08-19 | `pyproject.toml` (`mcp = ["mcp>=1.27,<2"]`) |
| A2 | Ausgabeschema-Bruch in `aiimaging_query_render` (`None`, wo ein String zugesagt war) | 🟩 **erledigt** | 2026-08-18 | `src/aiimaging/mcp_schemas.py` (`status` nullbar, mit dem Grund im Kommentar) |
| A3 | Kein `additionalProperties: false` in unseren Eingabeschemata | 🟩 **erledigt** | 2026-08-18 | `mcp_schemas.pruefe_vertrag` prüft es für **jeden** Vertrag, nicht einmalig von Hand |
| A4 | Klären, warum `/api/mcp/tools` keine Schemata durchreicht | 🟥 **offen** | — | **niemand** — braucht einen Blick ins Odysseus-Backend, den nur die HomeStation hat |
| A5 | `query_render` und `check_geometry` in `READ_ONLY_MCP_TOOLS` **beantragen** (`enqueue_render` ausdrücklich **nicht**) | 🟥 **offen** | — | `auftraege/offen/auf-20260826-48.json` |
| A6 | Rezept «AI-Imaging» beantragen: Konfiguration → `check_geometry` (Gate) → `enqueue_render` → `query_render` | 🟥 **offen** | — | `auftraege/offen/auf-20260826-48.json` |
| A7 | Feldnamen gegen den vorgesehenen Vorgänger prüfen | 🟩 **halb** | 2026-08-18 | `contracts.LANE_FIELDS` und `mcp_schemas.pruefe_verdrahtbarkeit` belegen die Verdrahtbarkeit **rechnerisch**; am laufenden Cockpit gemessen ist sie nicht (hängt an A4) |
| A8 | Wo erscheinen Bild und QA-Wert? Im Cockpit gibt es keinen Ort dafür | 🟩 **entschieden, nicht gebaut** | 2026-08-26 | In der **KosmoVis-Fläche**, nicht als neuer Anzeigetyp im fremden Knotenrahmen — der innere Graph bekommt eine innere Oberfläche. Begründung in `docs/OBERFLAECHE_KOSMOVIS.md` |
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
| B1 | Unseren Vertrag gegen `kosmovis.render-scene/v1` halten, an **einer** Stelle übersetzen | 🟩 **erledigt** | 2026-08-19 | `src/aiimaging/kosmo_szene.py` (`lies_szene`), `src/aiimaging/kosmo_naht.py` |
| B2 | Kameravertrag angleichen (`name`/`position`/`target`/`fov` gegen `blick_auf` und Brennweite in mm) | 🟩 **erledigt** | 2026-08-19 | `kosmo_szene.kamera_zu_spec`, `spec_zu_kamera`, `brennweite_zu_fov` |
| B3 | `kosmovis.render-result/v2` erzeugen, mit `spearman` und `geom_iou` einzeln | 🟩 **erledigt** | 2026-08-19 | `kosmo_szene.als_ergebnis` (`geometry_fidelity`, `spearman`, `geom_iou`, `threshold`) |
| B4 | **Der Arbeiter fehlt auf beiden Seiten** — die Brücke legt Dateien ab und wartet | 🟩 **erledigt** | 2026-08-22 | `src/aiimaging/abholer.py`, `tools/abholen.py`, `betrieb/kosmo-abholer.{service,timer}` |
| B5 | QA **je Kamera** ausweisen und die Verzeichniskonvention bedienen | 🟩 **halb** | 2026-08-23 | Je Kamera gemessen und in `befund.json` abgelegt; der **Vertrag** trägt weiterhin **ein** QA je Lauf (das schlechteste). Ein QA-Block je Kamera ist ihre Vertragsänderung — `auftraege/offen/auf-20260826-49.json` |
| B6 | Varianten: *n* Bilder je Lauf | 🟥 **offen** | — | Weder unsere Kette noch der fremde Vertrag kennen sie. `auftraege/offen/auf-20260826-49.json` |
| B7 | Den Treue-Regler `render.faithful` durchreichen | 🟩 **erledigt** | 2026-08-19 | `kosmo_szene.lies_szene` bildet ihn auf `controlnet_staerke` ab und sagt es in der Warnung |
| B8 | Ein über den **MCP-Einlass** bestellter Render wird auch ausgeführt | 🟩 **erledigt** | 2026-08-26 | `src/aiimaging/eigene_quelle.py`, `abholer.hole_einen(quelle=…)`, `tools/abholen.py --eigener-store` |

*B8 stand 2026-08-19 nicht auf der Liste, und das ist der unangenehmste Eintrag dieses
Blatts: Es fiel niemandem auf, dass die beiden Wege sich hier kreuzen. Weg A legte einen
Auftrag ab, Weg B hatte den einzigen Ausführer — und niemand las die Ablage von A. Ein
Knoten in KosmoOrbit konnte einen Render bestellen, der mit Freigabe auf `queued` ging und
dort blieb.*

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
