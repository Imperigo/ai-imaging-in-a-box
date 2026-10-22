# Visbox 0.3.39 — Fassungsblatt (22.10.2026)

**Codestand:** Fassung 0.3.39 auf `main` (Folgen aus Ergebnis 333 und der Mac-Prüfliste 0.3.35); Vorgänger 0.3.38 = Tag `v0.3.38`

**Grundlage:** Ergebnis 333; Mac-Prüfliste 0.3.35; Protokoll 74 §248–§249; Einbau-Stand C163 (erledigt), C164–C167;
Entscheid 126. Abgeglichen gegen alle Änderungen seit `v0.3.38` (`git log v0.3.38..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.39

Mit sichtbarem Himmel (Entscheid 126) wurde der Himmel auch bei «Mittag» nachtblau und bei «Abend» fast schwarz. Am Mac
zeigte die Stimmungskarte nach einem Vorschlag den alten Wert, und nach einem vollen Auftrag blieb «Grundlage veraltet»
stehen.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Der Himmel passt zur Stimmung: Mittag hell, Abend dämmrig — höchstens eine Blende dunkler, nie schwarz | 126 | gebaut, mit Probe; Messung 334 offen |
| Die Stimmungskarte, das Band und «Angewendet» nennen die Stimmung, die wirklich angewendet wird | — | gebaut, mit Probe |
| Nach einem vollen Auftrag steht kein «Grundlage veraltet» mehr; die Variante baut sofort darauf auf | — | gebaut, mit Probe |
| Die Auswertung am Heim-PC ist klein (KB statt 93 MB); die Rohmasken liegen gepackt daneben | — | gebaut, mit Probe |
| «Hang» und «steil» werden für das Bildmodell übersetzt | — | gebaut, mit Probe |
| Öffnungen ohne Art werden als Fenster erkannt, «gelaendeflaeche» als Gelände | — | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 334. Bestellungen mit Stimmung und sichtbarem
  Himmel rechnen einmal ein neues Grundbild (alte mit dunklem Himmel werden nicht wiederverwendet).

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Bei Mittag kann sich das Haus jetzt weniger vom hellen Himmel abheben — Messung 334 klärt das.
* Glas spiegelt im kleinen Bild (512 × 320) noch kaum sichtbar.
* Gleiche Grundbilder bekommen teils verschiedene Kennungen.
* Scheitert das Nachholen eines Bildes dreimal, kommt es erst beim nächsten Öffnen der Mappe.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
