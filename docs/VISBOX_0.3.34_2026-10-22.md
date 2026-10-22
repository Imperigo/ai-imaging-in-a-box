# Visbox 0.3.34 — Fassungsblatt (22.10.2026)

**Codestand:** Fassung 0.3.34 auf `main` (Varianten auf dem vorhandenen Grundbild, richtiges Urteil im Bildvergleich,
Export an Varianten); Vorgänger 0.3.33 = Tag `v0.3.33`

**Grundlage:** Ergebnisse 328 und 329; Protokoll 74 §229–§230; Einbau-Stand C140. Abgeglichen gegen alle Änderungen seit
`v0.3.33` (`git log v0.3.33..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.34

In der Demo-Kette rechnete jede Variante ihr Grundbild neu (dreieinhalb Minuten statt gut einer), der Bildvergleich
meldete «durchgefallen», wo nichts zu beurteilen war, und Varianten liessen sich nicht exportieren.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Eine Variante nutzt das Grundbild des Render-Knotens, wenn es passt — ein Startwert, kein neues Blender-Bild | 98a | gebaut, mit Probe; Messung 330 offen |
| «nicht beurteilbar» statt «durchgefallen», wenn zu wenig Haus im Bild ist | — | gebaut, mit Probe |
| Exportieren auch in der Grossansicht einer Variante; Dateiname mit dem Namen der Mappe | — | gebaut, mit Probe |
| Der Heim-PC sieht alle 10 s nach neuen Aufträgen statt alle 30 s | 127 | gebaut, mit Probe |

## Stand am Gerät

* **Heim-PC:** `git pull`, Dienst und Abholer neu starten, Takt neu einrichten (`betrieb/README.md`); dann Auftrag 330.
* **Mac:** Update-Knopf.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Der Bildvergleich zeigt eine Bestellung zugleich, nicht A und B nebeneinander.
* Beim Kuratieren erscheinen nur Bilder des Render-Knotens, nicht die Varianten.
* Der Kurations-Vorschlag denkt an Innenräume, auch beim Aussenbild.
* Die Grafikkarte ist bei 1600 × 1000 fast voll (≈ 31 von 32 GB).

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
