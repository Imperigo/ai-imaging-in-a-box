# Visbox 0.3.27 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.27 auf `main` (Assistent übernimmt Genanntes und sagt die Freigabe, Hausanteil ohne
unterste Bildzeile); Vorgänger 0.3.26 = Tag `v0.3.26`

**Grundlage:** Ergebnis 321; Protokoll 74 §218; Einbau-Stand C132. Abgeglichen gegen alle Änderungen seit `v0.3.26`
(`git log v0.3.26..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.27

Messung 321 bestätigte 0.3.26 am Gerät und fand im Assistenten drei Lücken, die vor der Demo zu schliessen sind: eine
genannte Güte fiel weg, die Freigabe blieb unerwähnt, und eine Bestellung konnte ohne Karte behauptet werden.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Was der Architekt ausdrücklich nennt (Stimmung, Güte, Grösse) und erlaubt ist, kommt auf die Render-Karte; kein doppelter Stimmungs-Knoten | — (321) | gebaut, mit Probe; Messung 322 offen |
| Jede Antwort mit Render-Karte sagt am Schluss, dass der Architekt freigibt | — (321) | gebaut, mit Probe |
| Ohne Karte meldet der Assistent keine Bestellung | — (321) | gebaut, mit Probe |
| Hausanteil: die unterste Bildzeile kann wieder Boden sein; Gründe ohne Fläche fallen aus der Liste | — (321) | gebaut, mit Probe |

## Stand am Gerät

* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 322.
* **Mac:** Update-Knopf.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Beim nahen Haus zählen Hecken und Weg weiter mit (≈ 0,56 gegen 0,46 von Hand); entschieden wird nach 322.
* Der obere, zurückgesetzte Baukörper fehlt im Hausanteil weiterhin.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
