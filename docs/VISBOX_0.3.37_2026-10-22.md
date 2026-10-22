# Visbox 0.3.37 — Fassungsblatt (22.10.2026)

**Codestand:** Fassung 0.3.37 auf `main` (Knotenschrift klebt beim Zoomen am Knoten); Vorgänger 0.3.36 = Tag `v0.3.36`

**Grundlage:** Owner-Befund am Mac auf 0.3.35; Entscheid 130 (R1); Protokoll 74 §245; Einbau-Stand C144 (Nachtrag).
Abgeglichen gegen alle Änderungen seit `v0.3.36` (`git log v0.3.36..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.37

Am Mac zitterte die Schrift in den Knoten beim Zoomen weiter und wechselte teils ihre Grösse. Gemessen: Der Knoten wurde
bei jedem Zoomschritt neu ausgelegt, beim Wechsel über 1 auf einem anderen Weg gezeichnet, und die Kopf- und
Anschlussschrift wurde in Bildschirmgrösse gerundet.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Ein Weg für alle Zoomstufen: der Knoten wird als Ganzes verkleinert und vergrössert, Schrift und Umbruch bleiben gleich; scharf wird es erst nach dem Loslassen | 130 (R1) | gebaut, mit Probe (Chromium); am Mac unbestätigt |
| Kopf- und Anschlussschrift ohne Rundung, Bedienelemente ebenso | 130 (R1) | gebaut, mit Probe |
| 3D-Fenster im Knoten bauen sich nicht mehr bei jedem Zoomschritt neu auf | — | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf; dann langsam zwischen halber und doppelter Grösse zoomen.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Geprüft ist nur in Chromium; ob WebKit am Mac genauso auslegt, zeigt erst der Blick am Gerät. Springt nach dem
  Loslassen über 1 einmal etwas, ist der Ausweg «Ruhe statt Schärfe».
* Bei doppelter Grösse überlappt die Kopfzeile des Prompt-Kombinierers den Pfeil-Knopf — das löst «Knoten im Massstab».

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
