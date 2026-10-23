# Visbox 0.3.51 — Fassungsblatt (23.10.2026)

**Codestand:** Fassung 0.3.51 auf `main` (Folgen aus der Mac-Nachprüfung mit 0.3.50); Vorgänger 0.3.50 = Tag `v0.3.50`

**Grundlage:** Mac-Nachprüfung 0.3.50 und iPad-Simulator; Protokoll 74 §268–§270; Einbau-Stand C188, C189.
Abgeglichen gegen alle Änderungen seit `v0.3.50` (`git log v0.3.50..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.51

Bei einem Haus mit Holzlattung und schmalem Fensterband malte die Variante das Band zu, und die Prüfung meldete
trotzdem «bestanden». Im iPad-Simulator liess sich nicht zeichnen.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Neue Prüfung «Fenster gehalten»: übermalt eine Variante mehr als die Hälfte des Glases, steht es in den Hinweisen | 138 | gebaut, mit Probe; Messung 346 offen |
| Zwei Schalter für den Prompt (Glas-Satz, Stoff seltener nennen) — vorerst aus, Bilder unverändert | 138 | gebaut, mit Probe; Messung 346 offen |
| Im iPad-Simulator zeichnet jede Berührung; am iPad weiter nur der Stift | 4 | gebaut, mit Probe |
| Erklärkarten je Knoten der Knotenansicht (Tafel) | — | erzeugt |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 346. Kein Bild und kein Prompt ändert sich;
  neu ist die Fensterprüfung (rund 1,6 s je Kamera).

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Das Fensterband bei Holzlattung kann in der Variante weiterhin übermalt werden; was dagegen hilft, misst Auftrag 346.
* Die Grenzwerte der Fensterprüfung sind gesetzt, nicht gemessen; Glas ohne Glaswort im Materialnamen sieht sie nicht.
* Bei 1600 × 1000 rechnet die KI 1600 × 992 und wird gestreckt — leicht weicher.
* Am iPad zeichnet ohne Stift weiterhin nichts (Owner-Frage «Mit dem Finger zeichnen»).

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
