# Visbox 0.3.56 — Fassungsblatt (24.10.2026)

**Codestand:** Fassung 0.3.56 auf `main` (dringender Owner-Auftrag Vollautomatik; Fläche «Mitschauen und Bedienen»); Vorgänger 0.3.55 = Tag `v0.3.55`

**Grundlage:** Owner-Auftrag 24.10. (Klickfrage Variante A); Protokoll 74 §282–§283; Einbau-Stand C200, C201;
Entscheide 134 (geändert), 146. Abgeglichen gegen alle Änderungen seit `v0.3.55` (`git log v0.3.55..` ohne
Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.56

In «Voll» musste der Owner trotzdem jede Karte anwenden und jedes Bild freigeben — für ein Bild aus der Skizze vier
Klicks. Die Fläche «Mitschauen und Bedienen» war zu schmal und zeigte in «Voll» den Karten-Satz.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| In «Voll» rechnen Bild, Varianten und Grundbild ohne Karte und ohne «Freigeben»; jeder Schritt steht im Verlauf und lässt sich zurücknehmen; «Alle anhalten» bleibt | 146 | gebaut, mit Probe; Messung 351 und Mac offen |
| Grenzen setzt der Heim-PC selbst durch: höchstens 5 Läufe pro Stunde ohne Klick, nie ein Bildmodell mit offener oder Forschungslizenz, Löschen bleibt eine Karte | 146 | gebaut, mit Probe; Messung 351 offen |
| Neues Werkzeug für Claude: «Grundlage rendern» | 146 | gebaut, mit Probe |
| `visbox_status` und die Werkzeugtexte sagen je Modus, was ohne Klick geht («n von 5») | 146 | gebaut, mit Probe |
| Fläche «Mitschauen und Bedienen»: Schalter neben den Wörtern, kein Umbruch, Satz je Modus | 115 | gebaut, mit Probe; am Mac offen |

## Stand am Gerät

* **Mac:** Update-Knopf (danach iPad nicht neu koppeln nötig, wenn bei der Passwortfrage «Erlauben» gewählt wird).
  Prüfen: «Voll» einstellen, Claude «Mach aus der neuesten Skizze ein Bild» — kein Klick; `visbox_status` zeigt «1 von 5».
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 351.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Rendern über die Maus bleibt in «Voll» eine Karte.
* Der Heim-PC kann einen echten Klick nicht von einer Freigabe eines angemeldeten Programms unterscheiden (wie bisher).
* Die Legende der Knotenansicht kann beim Zoomen noch hinter Knoten geraten — Fix folgt mit der nächsten Fassung.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
