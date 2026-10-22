# Visbox 0.3.31 — Fassungsblatt (22.10.2026)

**Codestand:** Fassung 0.3.31 auf `main` (mehrere Vorschläge ohne Doppel, Freigabesatz in der Mehrzahl);
Vorgänger 0.3.30 = Tag `v0.3.30`

**Grundlage:** Ergebnis 325; Protokoll 74 §222; Einbau-Stand C136. Abgeglichen gegen alle Änderungen seit `v0.3.30`
(`git log v0.3.30..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.31

Messung 325 bestätigte 0.3.30: Eine Frage mit zwei Vorschlägen nennt beide. Zwei Kleinigkeiten zur Lesbarkeit blieben —
ein Vorschlag stand doppelt, und der Freigabesatz sprach von «der Karte» bei zweien.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Bei mehreren Vorschlägen steht keiner doppelt | — (325) | gebaut, mit Probe; Messung 326 offen |
| Der Freigabesatz steht bei mehreren Vorschlägen in der Mehrzahl | — (325) | gebaut, mit Probe |

## Stand am Gerät

* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 326.
* **Mac:** Update-Knopf.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Beim nahen Haus zählen Hecken weiter mit (≈ 0,55 gegen 0,46 von Hand); Trennung nach Art nach der Demo.
* Der obere, zurückgesetzte Baukörper fehlt im Hausanteil weiterhin.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
