# Visbox 0.3.40 — Fassungsblatt (22.10.2026)

**Codestand:** Fassung 0.3.40 auf `main` (Folgen aus Ergebnis 334); Vorgänger 0.3.39 = Tag `v0.3.39`

**Grundlage:** Ergebnis 334; Protokoll 74 §250; Einbau-Stand C167 (erledigt), C168–C170; Entscheid 126. Abgeglichen
gegen alle Änderungen seit `v0.3.39` (`git log v0.3.39..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.40

Messung 334 bestätigte den hellen Mittags- und den dämmrigen Abendhimmel, zeigte aber unter dem Horizont ausserhalb der
Geländeplatte die untere Hälfte des Himmelsbilds statt Boden.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Unter dem Horizont steht Boden bis zum Horizont, mit weichem Dunst am Übergang — kein gespiegelter Himmel mehr | 126 | gebaut, mit Probe; Messung 335 offen |
| Der Bericht nennt, wenn das Gelände am Namen vom Gebäude getrennt wurde | — | gebaut, mit Probe |
| Der Kontrast Haus/Himmel wird zusätzlich am KI-Bild gemessen | — | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 335. Bestellungen mit sichtbarem Himmel rechnen
  einmal ein neues Grundbild.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Die Bodenfarbe ist gesetzt, nicht gemessen: Zwischen sonnenbeschienener Platte und Boden kann eine Naht sichtbar sein.
* Glas spiegelt im kleinen Bild noch kaum sichtbar.
* Gleiche Grundbilder bekommen teils verschiedene Kennungen.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
