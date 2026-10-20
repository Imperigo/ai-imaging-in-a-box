# Visbox 0.3.3 — Fassungsblatt (20.10.2026)

**Codestand:** Fassung 0.3.3 auf `main` (Varianten ohne erneutes Hochladen, Heim-PC ohne Stocken, Gelände wieder
rechenbar, eigener Assistent); Vorgänger 0.3.2 = Tag `v0.3.2`

**Grundlage:** Owner-Befund am Mac 20.10.2026 («Variante erzeugen» → «nicht rechtzeitig geantwortet»); Ergebnisse der
HomeStation `auf-20261020-290` und `-288`; Entscheide 105, 106d; Protokoll 74 §150

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.3

Am Mac brach «Variante erzeugen» ab: Jede Variante schickte das ganze Modell nochmals, und der Heim-PC hielt dabei
alles andere an. Die Messung der HomeStation fand dazu, dass Szenen mit Geländeplatte und Auto-Kamera nie gerechnet
wurden und eine doppelte Kamera nicht mehr erkannt wurde.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Heim-PC: Eine Variante mit Grundlage braucht kein Modell mehr; der Heim-PC nimmt es aus der Grundlage. Kennt er die Grundlage nicht, sagt er es (409) | Owner-Befund 20.10. | gebaut, mit Probe; am Gerät unbestätigt (Auftrag 291) |
| Heim-PC: Hochladen und grosse Dateien halten den Dienst nicht mehr an; das Modell wird stückweise gelesen und geschrieben | Owner-Befund 20.10. | gebaut, mit Probe; am Gerät unbestätigt |
| Mac: Hochladen eines Auftrags und «Datei laden …» dürfen 5 Minuten dauern, alles andere weiter 25 s | Owner-Befund 20.10. | gebaut, mit Probe; am Gerät unbestätigt |
| Heim-PC: Szenen mit Geländeplatte und Auto-Kamera werden wieder gerechnet (die Prüfung zog den Hausanteil doppelt ab) | auf-290 | behoben, mit Probe |
| Heim-PC: Eine doppelte Kamera (gleiche Ansicht) wird auch mit Randrauschen erkannt und nur einmal gerechnet | auf-290 | behoben, mit Probe |
| Heim-PC: Ein widersprüchlicher Auftrag (Güte mit «nur Grundlage» u. a.) endet sofort mit Satz, statt alle 30 s neu gelesen zu werden | auf-290 | behoben, mit Probe |
| Heim-PC: Der Abbruchsatz steht im Auftrag | auf-290 | behoben, mit Probe |
| Heim-PC: Die Nullprobe der Prüfung wird je Grundlage gemerkt — weitere Varianten sind schneller, die Prüfung bleibt gleich | 104a | gebaut, mit Probe; Zeit ungemessen |
| Assistent: eigenes Modell `qwen3:14b`; Visbox entlädt nur dieses, nie ein Kosmo-Modell | 106d | gebaut, mit Probe; am Gerät braucht es `ollama pull qwen3:14b` |
| Abholer: Hält nur das Assistenten-Modell die Karte und läuft keine Frage, entlädt er es, statt zu warten | 106d, Auflage HomeStation | gebaut, mit Probe |
| Mac: Der Satz zu Claude unter «Wer rechnet?» sagt jetzt, was stimmt: «wird eingerichtet» | 105 | gebaut, mit Probe |

## Stand am Gerät

* **Heim-PC:** nach `git pull` Dienst und Abholer neu starten; `ollama pull qwen3:14b`; Auftrag 291 misst nach.
* **Mac:** Update-Knopf. Die Knotenansicht schickt das Modell bei einer Variante noch mit, bis die neue Knotenansicht
  kommt — dank längerer Wartezeit und eines Heim-PC ohne Stocken sollte es trotzdem durchgehen.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* **Am Gerät nicht geprüft.**
* **Die Knotenansicht lässt das Modell erst mit der nächsten Fassung weg**; bis dahin geht jede Variante noch mit
  Modell hinauf.
* Die Vorschau zeigte in Auftrag 290 Innenräume statt eines Hauses (Hausanteil 10–12 %): Das ist ein Befund zum
  Bildmodell und zum Prompt, kein Fehler im Ablauf; die Geometrie-Prüfung meldet es richtig.
* Ohne `qwen3:14b` am Heim-PC zeigt der Assistent «fehlt».

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
