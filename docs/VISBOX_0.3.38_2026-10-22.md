# Visbox 0.3.38 — Fassungsblatt (22.10.2026)

**Codestand:** Fassung 0.3.38 auf `main` (Folgen aus dem Mac-Demolauf «Haus am Hang»); Vorgänger 0.3.37 = Tag `v0.3.37`

**Grundlage:** Demolauf «Haus am Hang» (N1–N10), Ergebnis 332; Protokoll 74 §246–§247; Einbau-Stand C158 (erledigt),
C160–C163; Entscheide 136, 137. Abgeglichen gegen alle Änderungen seit `v0.3.37` (`git log v0.3.37..` ohne
Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.38

Im Demolauf «Haus am Hang» blieb eine am Mac angelegte Mappe nach «Datei laden …» leer und entstand am Heim-PC doppelt,
ein fertiges Bild kam nicht am Mac an, und eine Mittag-Variante wurde auf dem Abend-Grundbild zur Nacht.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| «Datei laden …» in einer Mac-Mappe legt Modell und Auswertung in genau diese Mappe — keine doppelte Mappe mehr | 129 | gebaut, mit Probe |
| Beim Öffnen einer Mappe holt die App Bilder nach, die am Heim-PC fertig, am Mac aber noch nicht angekommen sind | — | gebaut, mit Probe |
| Eine Variante mit anderer Stimmung bekommt ihr eigenes Grundbild — Himmel und Licht folgen ihrer Stimmung | 126 | gebaut, mit Probe; Messung 333 offen |
| Bauteile ohne Art behalten ihr benanntes Material (kein Holz mehr auf Beton und Bäumen) | — | gebaut, mit Probe |
| Glas ist glatt und spiegelt | — | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 333.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Eine Variante mit anderer Stimmung braucht jetzt ein neues Grundbild und dauert darum länger als eine Variante mit
  gleicher Stimmung.
* Ein nachgeholtes Bild liegt in der Mappe, erscheint aber erst nach dem Neuladen des Laufs im Raster.
* Die schon doppelte Mappe muss von Hand gelöscht werden.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
