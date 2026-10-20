# Visbox 0.3.4 — Fassungsblatt (20.10.2026)

**Codestand:** Fassung 0.3.4 auf `main` (Knotenansicht: Fokus, ruhiges Bild beim Zoomen, Variante ohne Modell);
Vorgänger 0.3.3 = Tag `v0.3.3`

**Grundlage:** Owner-Befunde am Mac 20.10.2026 (Textfeld mit verrutschtem Farbrand, Vorschaubild springt beim Zoomen,
«Variante erzeugen» → «nicht rechtzeitig geantwortet»); Protokoll 74 §152

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.4

Die Knotenansicht hatte drei Fehler, die der Owner am Mac sah. Seit 0.3.3 nimmt der Heim-PC eine Variante ohne Modell
an; jetzt schickt die Knotenansicht es auch nicht mehr mit.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Knoten: Textfelder und Auswahlen zeigen den Fokus als Rand in der Akzentfarbe statt als abgeschnittenen Ring | Owner-Befund 20.10. | behoben, mit Probe; am Gerät unbestätigt |
| Knoten: Das Bild im Render-Knoten hat eine feste Box und springt beim Rein- und Rauszoomen nicht mehr | Owner-Befund 20.10. | behoben, mit Probe (Chromium); in WebKit am Gerät unbestätigt |
| Knoten: Eine Variante mit Grundlage schickt kein Modell mehr; der Auftrag darf 5 Minuten zum Ankommen brauchen, alles andere 30 s | Owner-Befund 20.10. | gebaut, mit Probe; am Gerät unbestätigt |
| Knoten: Kennt der Heim-PC die Grundlage nicht, geht die Variante einmal mit Modell hinaus, mit Hinweissatz | Owner-Befund 20.10. | gebaut, mit Probe |
| Knoten: Die bestellte Güte steht ab dem Absenden am Lauf und geht mit in die Übersicht der Bilder | 104a | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf, dann in den Prompt klicken, rein- und rauszoomen, «Variante erzeugen» auf einer Grundlage.
* **Heim-PC:** `git pull`; am Rechnen ändert sich nichts.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* **Am Gerät nicht geprüft**, das ruhige Bild nur in Chromium gemessen.
* Die Felder im Knoten bleiben rund (16 px): Ein eckigeres Feld verbietet die Form-Regel des Hauses ohne Owner-Entscheid.
* Die Varianten zeigen ihre Bilder noch nicht als kleine Vorschau im Knoten — das wird zuerst gezeichnet.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
