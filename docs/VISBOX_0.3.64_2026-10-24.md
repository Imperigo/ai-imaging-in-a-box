# Visbox 0.3.64 — Fassungsblatt (24.10.2026)

**Codestand:** Fassung 0.3.64 auf `main` (Umfeld am Bau, den die Kamera zeigt); Vorgänger 0.3.63 = Tag `v0.3.63`

**Grundlage:** Ergebnis 361; Entscheid 150 (Lesart Blickziel); Protokoll 74 §288 (Nachtrag 361); Einbau-Stand C205;
Auftrag 362. Abgeglichen gegen alle Änderungen seit `v0.3.63` (`git log v0.3.63..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.64

Messung 361: Alle Bäume standen beim grössten Bau im Bild — der war aber nicht der Bau mit Innenhof, auf den die
Kamera zielte. Beim Bau mit Innenhof stand kein einziger Baum.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Bei grossen Anlagen ist der Hauptbau der Bau, auf den die Kamera zielt (nicht der grösste); nur ohne Blickziel der grösste | 150 | gebaut, mit Probe; Messung 362 offen |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 362.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Zielt die Kamera auf eine Lücke zwischen Bauten, gilt der nächstgelegene Bau.
* Das Wettbewerbsmodell enthält nur Grundriss-Platten; die KI bleibt daran schwach.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
