# Visbox 0.3.28 — Fassungsblatt (22.10.2026)

**Codestand:** Fassung 0.3.28 auf `main` (Assistent spricht zum Architekten ohne interne Texte und Werkzeugnamen);
Vorgänger 0.3.27 = Tag `v0.3.27`

**Grundlage:** Ergebnis 322; Protokoll 74 §219; Einbau-Stand C133. Abgeglichen gegen alle Änderungen seit `v0.3.27`
(`git log v0.3.27..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.28

Messung 322 bestätigte 0.3.27 am Gerät. Übrig blieben Stellen, an denen der Assistent dem Architekten Texte zeigte,
die nur für das Sprachmodell gedacht waren — für die Demo sichtbar und darum vorher zu schliessen.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Interne Abweisungstexte und Werkzeugnamen erscheinen nicht mehr in der Antwort; statt dessen ein Alltagswort | — (322) | gebaut, mit Probe; Messung 323 offen |
| Verneinte Sätze («ist noch nicht gestellt») bleiben stehen | — (322) | gebaut, mit Probe |
| Zwischensätze («Weggelassen …») nur bei einem Schritt, der wirklich ausgeführt wird | — (322) | gebaut, mit Probe |
| Einheitlich «der Architekt» | — (322) | gebaut, mit Probe |

## Stand am Gerät

* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 323.
* **Mac:** Update-Knopf.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Beim nahen Haus zählen Hecken weiter mit (≈ 0,55 gegen 0,46 von Hand). Eine Grenze über Entfernung oder über die
  Spalten der Grundlage schnitte Teile des Hauses ab; eine Trennung nach Art (Pflanzen) folgt nach der Demo.
* Der obere, zurückgesetzte Baukörper fehlt im Hausanteil weiterhin.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
