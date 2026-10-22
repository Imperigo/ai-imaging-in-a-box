# Visbox 0.3.29 — Fassungsblatt (22.10.2026)

**Codestand:** Fassung 0.3.29 auf `main` (Assistent nennt jeden Vorschlag, richtiger Fall bei «der Architekt»);
Vorgänger 0.3.28 = Tag `v0.3.28`

**Grundlage:** Ergebnis 323; Protokoll 74 §220; Einbau-Stand C134. Abgeglichen gegen alle Änderungen seit `v0.3.28`
(`git log v0.3.28..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.29

Messung 323 bestätigte 0.3.28 am Gerät. Übrig blieb ein Vorschlag, den die Antwort nicht nannte, und ein falscher Fall
beim Wort «Architekt» — beides in der Demo sichtbar.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Ergibt eine Frage zwei oder mehr Vorschläge, nennt die Antwort jeden | — (323) | gebaut, mit Probe; Messung 324 offen |
| «des Architekten» und «dem Architekten» je nach Fall | — (323) | gebaut, mit Probe |
| Nach dem Gedankenstrich geht der Satz klein weiter | — (323) | gebaut, mit Probe |

## Stand am Gerät

* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 324.
* **Mac:** Update-Knopf.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Beim nahen Haus zählen Hecken weiter mit (≈ 0,55 gegen 0,46 von Hand); Trennung nach Art nach der Demo.
* Der obere, zurückgesetzte Baukörper fehlt im Hausanteil weiterhin.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
