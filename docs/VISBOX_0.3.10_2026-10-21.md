# Visbox 0.3.10 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.10 auf `main` (Abend mit Kontrast, Warnsatz bei unkenntlichem Haus, Abgleich im Bau); Vorgänger 0.3.9 = Tag `v0.3.9`

**Grundlage:** Entscheid 115; Plan `docs/PLAN_UI_GLEICHHEIT_2026-10-20.md` (Stufe S5); Befunde aus Auftrag
`auf-20261020-295`; Protokoll 74 §163–§166; Einbau-Stand C92–C94

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.10

Die Messung 295 bestätigte das seitliche Licht, zeigte aber am Abend ein Haus, das sich zu wenig abhebt, und ein
KI-Bild, dessen Haus nicht wiederzuerkennen war, ohne dass eine Zahl warnte.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Die Vorprobe misst das Haus so, wie die Prüfung es misst: der Abend hebt das Haus vom Hintergrund ab | — (295) | gebaut, mit Probe; Messung 296 offen |
| Satz «Haus im KI-Bild nicht wiederzuerkennen», wenn die Geometrie fast nicht mehr passt | — (295) | gebaut, mit Probe |
| Das Ergebnis nennt die wirkliche Drehung des Himmelsbilds je Kamera, immer zwischen 0 und 360 Grad | — (295) | gebaut, mit Probe |
| Der Vermerk «Vorschau» steht auch an Bildkarte, Vergleich, Inspektor und Blatt-Knoten | 115 | gebaut, mit Probe; am Gerät unbestätigt |
| Der Bau der Knotenansicht prüft die Kopie gegen die Vorlage und bricht bei Abweichung ab | 115 | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf. Danach eine Vorschau bestellen und den Vermerk «Vorschau» an der Bildkarte ansehen.
* **Heim-PC:** `git pull`; mit Stimmung werden gespeicherte Grundlagen neu gerechnet, am Abend wird der Hintergrund
  dunkler. Ohne Stimmung bleibt das Grundbild gleich.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Die KI baut in allen geprüften Bildern über den Umriss des Hauses hinaus und malt Sichtbeton nur teilweise; das ist
  gemessen, aber noch nicht behoben.
* Schlagschatten sind auf Augenhöhe kaum zu sehen.
* Kugel, Gespräch und Einstellungs-Insel aus 0.3.9 sind am Gerät weiter unbestätigt.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
