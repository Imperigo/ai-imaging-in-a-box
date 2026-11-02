# Visbox 0.3.74 — Fassungsblatt (02.11.2026)

**Codestand:** Fassung 0.3.74 auf `main` (Skizzen-Fassung: «Bild aus Skizze» vom frischen Render, Bildwerkzeuge
gesperrt bis zur Messung); Vorgänger 0.3.73 = Tag `v0.3.73`

**Grundlage:** Owner-Entscheid 31.10.2026 «Immer vom Render» und Owner-Freigabe 02.11.2026 (Einspielen und
Veröffentlichen von 0.3.74); gegengelesen grün: A0093 (G-A0093), A0094 (G-A0094, mit Auflage, die in dieser Runde
erfüllt ist). Abgeglichen gegen alle Änderungen seit `v0.3.73` (`git log v0.3.73..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.74

Seit «Immer vom Render» bestellt die Knotenansicht ein «Bild aus Skizze» so, dass zuerst eine frische Grundlage vom
Standpunkt der Skizze gerechnet wird. Die Visbox liess solche Bestellungen bisher als unbekannt liegen. Zugleich bot
die Visbox-Seite noch alle Bildwerkzeuge und die Vorschau an, obwohl nur eines nachweislich vom Render startet.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Bild aus Skizze vom frischen Render: Eine Skizze mit «frisch» rechnet zuerst die Blender-Grundlage vom Standpunkt der Skizze; deren Bild ist das Startbild, die Skizze liegt darauf und führt, ihre Anweisung ist der Auftrag (A0094) | 31.10. | gebaut, mit Probe; am Heim-PC offen |
| Unpassende Skizzen-Bestellungen (mehrere Kameras, keine Kamera, alte Grundlage) werden mit Satz abgewiesen statt still anders gerechnet (A0094) | 31.10. | gebaut, mit Probe |
| Maske, Deckung und Prüfung lesen das reine Render-Bild, nicht den Strich der Skizze (Auflage zu A0094) | — | gebaut, mit Probe |
| Bildwerkzeuge gesperrt: nur Z-Image Turbo wählbar, Qwen-Image 2.1 und die übrigen gesperrt bis zur Messung, die Vorschau ebenso; die Absage kommt schon in der Seite (A0093) | 31.10., E128, E146, E153 | gebaut, mit Probe; am Mac offen |
| Ein Modellkürzel ohne Eintrag bei uns endet beim Annehmen mit Satz, statt liegen zu bleiben (A0093) | — | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf, danach Visbox ganz beenden und neu starten. Prüfen: `visbox_status` nennt 0.3.74; in der
  Knotenansicht ist nur Z-Image Turbo wählbar, die Vorschau ist gesperrt.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten. Danach «Bild aus Skizze» einmal Ende zu Ende bestellen.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* **Blender-Lauf Ende zu Ende am Gerät steht aus:** Der Weg «Skizze auf frischer Grundlage» ist nur mit Attrappen
  geprüft (ohne Blender und GPU).
* **Skizze nach einem «frisch»-Lauf nicht als gerechnet vermerkt:** Anders als der bisherige Skizzenweg hält ein
  Lauf mit frischer Grundlage die Skizze nicht als gerechnet fest.
* **Kontext, Umfeld und Stimmung bleiben bei Skizzen gesperrt**, auch mit frischer Grundlage; der Satz zum Umfeld
  nennt dafür noch den Grund des alten Skizzenwegs.
* **Die Vorschau ist nur in der Seite gesperrt:** Wer die Brücke direkt anspricht (POST ohne Seite), kann sie weiter
  bestellen.
* Die neuen Proben der Mac-App (XCTest) sind am Mac noch nicht gelaufen.

## Prüfung

Volle Suite ohne GPU, grün; Vitest aller Pakete der Knotenansicht grün; Bau der Knotenansicht neu gebaut und zweimal
gleich (Prüfsummen). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job `freigabe` legt die Freigabe erst
auf `main` an.
