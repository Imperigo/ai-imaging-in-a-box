# Visbox 0.3.7 — Fassungsblatt (20.10.2026)

**Codestand:** Fassung 0.3.7 auf `main` (Claude bedient Visbox am Mac); Vorgänger 0.3.6 = Tag `v0.3.6`

**Grundlage:** Entscheide 105–106f, 108, 114; Plan `docs/PLAN_KI_BEDIENUNG_2026-10-20.md` (Stufen 3 und 4, Teil);
Blatt 30 der Entwurfsfläche; Protokoll 74 §156

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.7

Der Owner will Visbox voll mit Claude bedienen können (Entscheid 105). Bis 0.3.6 antwortete die App Claude nur mit
ihrem Stand; jetzt kann Claude in der Knotenansicht arbeiten — mit Vorschlägen, die der Architekt annimmt.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Claude (Claude Code oder Claude Desktop) bedient die Knotenansicht über MCP, nur auf diesem Mac: Knoten lesen, setzen, verbinden, einstellen, löschen; Grundlage und Varianten bestellen | 105, 106 | gebaut, mit Probe; am Gerät unbestätigt |
| Claude liest Mappe und Skizzen, sieht Bilder an und kann einen Lauf abbrechen | 105, 106f | gebaut, mit Probe; am Gerät unbestätigt |
| Vorschläge der KI erscheinen als Karten in der Assistent-Leiste, mit Anwenden und Ablehnen | 106a | gebaut, mit Probe; am Gerät unbestätigt |
| Selbständigkeit «Karte · Coop · Voll» oben in der Leiste; Löschen und Rendern immer als Karte; die Grafikkarte gibt nie die KI frei | 106b, 106c, 108 A | gebaut, mit Probe |
| «Claude arbeitet …» steht nur, solange die KI arbeitet | 108 C | gebaut, mit Probe |
| Claudes Schritte haben einen eigenen Rückgängig-Weg: Strg+Z nimmt nur deine Schritte zurück, «Claudes letzten Schritt zurücknehmen» die der KI | 114 | gebaut, mit Probe; am Gerät unbestätigt |
| Einrichten › «Claude über MCP»: an/aus (ab Werk an), Befehl zum Verbinden, «Visbox hinzufügen» für Claude Desktop, Hinweis, was an Anthropic geht | 106e, 106f, 108 B | gebaut, mit Probe; am Gerät unbestätigt |

## Stand am Gerät

* **Mac:** Update-Knopf. Dann im Terminal einmal
  `claude mcp add --transport http visbox http://127.0.0.1:8631/mcp`, in Claude Code `/mcp` — «visbox» steht als
  verbunden. Für Claude Desktop: Einrichten › «Claude über MCP» › «Visbox hinzufügen», Claude Desktop neu starten.
* **Heim-PC:** `git pull`; am Rechnen ändert sich nichts.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* **Am Gerät nicht geprüft** — weder Claude Code noch Claude Desktop haben Visbox bisher wirklich bedient.
* Hat Claude im Modus Coop an einem Render-Graphen gearbeitet, sperrt Strg+Z auch ältere eigene Schritte am selben
  Graphen, bis Claudes Schritt zurückgenommen ist.
* Modell laden, Kameras vorschlagen, Verlauf lesen, Mappe anlegen und Bild ausgeben kann Claude erst, wenn die Mappe am
  Mac liegt.
* Der Assistent in der Leiste nutzt diese Werkzeuge noch nicht (Stufe 5).

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
