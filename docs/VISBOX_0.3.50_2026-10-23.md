# Visbox 0.3.50 — Fassungsblatt (23.10.2026)

**Codestand:** Fassung 0.3.50 auf `main` (Folgen aus R57 und dem Nachtrag S7 zu Ergebnis 345); Vorgänger 0.3.49 = Tag `v0.3.49`

**Grundlage:** Geräteprobe R57; Ergebnis 345 (Nachtrag S7, echter IFC-Export mit Gelände); Protokoll 74 §266–§267;
Einbau-Stand C184 (erledigt), C186, C187. Abgeglichen gegen alle Änderungen seit `v0.3.49` (`git log v0.3.49..` ohne
Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.50

Der echte IFC-Export mit Gelände läuft durch (S7 grün); zwei Sätze im Bericht klangen dabei wie Fehler, obwohl alles
richtig lief.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Ein Gelände, das die Datei selbst als Boden ausweist, erscheint im Bericht als Auskunft («Gelände aus der Datei: …»), nicht als Warnung | — | gebaut, mit Probe |
| Der Befund «kaum sichtbar» folgt derselben Regel wie die Warnung (Kontrast am Umriss) | — | gebaut, mit Probe |
| Bestellsätze der Knotenansicht können einer Vollautomatik folgen; in Visbox bleibt «wartet auf Freigabe» | 106b, 134 | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten. Kein Bild und kein Ablauf ändert sich.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Im IFC-Weg wirken die Fenster hell (Durchsicht nach innen), im glb-Weg dunkel — nach der Demo.
* Kameras im Modus «Auto» stehen rund 1,3 m über dem Gelände (Owner-Frage nach der Demo).

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
