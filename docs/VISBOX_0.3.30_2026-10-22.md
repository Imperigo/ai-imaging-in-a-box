# Visbox 0.3.30 — Fassungsblatt (22.10.2026)

**Codestand:** Fassung 0.3.30 auf `main` (Assistent nennt «die Nutzerin» den Architekten, mehrere Vorschläge in einer Form);
Vorgänger 0.3.29 = Tag `v0.3.29`

**Grundlage:** Ergebnis 324; Protokoll 74 §221; Einbau-Stand C135. Abgeglichen gegen alle Änderungen seit `v0.3.29`
(`git log v0.3.29..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.30

Messung 324 bestätigte 0.3.29. Das Sprachmodell sprach diesmal von «der Nutzerin», und der Satz zu mehreren Vorschlägen
stand in zwei Formen — beides vor der Demo geglättet.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| «die Nutzerin» / «der Nutzer» heisst in der Antwort «der Architekt» | — (324) | gebaut, mit Probe; Messung 325 offen |
| Mehrere Vorschläge in einer Form und in der Mehrzahl genannt | — (324) | gebaut, mit Probe |

## Stand am Gerät

* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 325.
* **Mac:** Update-Knopf.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Beim nahen Haus zählen Hecken weiter mit (≈ 0,55 gegen 0,46 von Hand); Trennung nach Art nach der Demo.
* Der obere, zurückgesetzte Baukörper fehlt im Hausanteil weiterhin.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
